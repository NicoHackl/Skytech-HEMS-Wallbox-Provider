"""hems_bridge.py — Betriebsart, HEMS-Anbindung und Befehlsfolge an die Wallbox.

Vertrag: `contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md`. Die
Abschnitte, die hier umgesetzt sind:

- **Betriebsart** (D-005): Schalter „HEMS Steuerung" an → Sollwert aus den zwei HEMS-Helfern;
  aus → aus den manuellen Entities. Ohne HEMS-Präfix immer manuell.
- **Lebenszeichen** (D-004): Im HEMS-Betrieb gilt ein Sollwert nur bei frischem
  `sensor.skytech_hems_status`; sonst Stopp. Nach dem Start erst nach einem frisch gesehenen Zyklus.
- **Validierung**: Ungültiger Strom oder (bei `automatisch`) ungültige Phasenzahl → Stopp und
  Fehlerstatus; nie auf einen anderen positiven Wert runden.
- **Befehlsfolge** (D-003): Stopp = Freigabe aus. Positiv = [Phasenmodus, falls geändert] →
  Strom → Freigabe ein, ohne Zwischenwert und ohne Bestätigung („durchreichen").
- **Stoppvorrang**: Vor jedem positiven Einzelschritt wird der wirksame Sollwert neu gebildet;
  weicht er ab, entfallen die restlichen Schritte und die Folge beginnt mit dem neuesten Wert.
  Der Transport sperrt nur je Einzelzugriff — ein Stopp wartet höchstens auf einen Schreibvorgang.
- **Neuschreiben**: Der wirksame Sollwert wird alle `keepalive_s` erneut geschrieben, auch nach
  einem Schreibfehler. Der Fehler bleibt sichtbar, bis ein Schreibvorgang gelingt.

Der Phasenmodus wird nur geschrieben, wenn er vom zuletzt erfolgreich geschriebenen abweicht —
nach dem Start also einmal. Das Neuschreiben fasst ihn sonst nicht an, damit die Wallbox nicht
bei jedem Takt einen Umschaltwunsch erhält.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.core import Event, HomeAssistant, State
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval

from .adapters.base import WallboxAdapterError
from .const import (
    FALLBACK_MAX_CURRENT_A,
    HEARTBEAT_CHECK_INTERVAL,
    PHASE_MODE_AUTOMATIC,
)
from .heartbeat import STATUS_ENTITY_ID, HemsHeartbeat

if TYPE_CHECKING:
    from .coordinator import WallboxCoordinator

_LOGGER = logging.getLogger(__name__)

SOURCE_HEMS = "hems"
SOURCE_MANUAL = "manuell"

# Normalisierter Steuerstatus (Sensor „Steuerung", additive Diagnose zum Vertrag).
STATUS_HEMS = "hems"
STATUS_MANUAL = "manuell"
STATUS_NO_HEARTBEAT = "kein_hems_lebenszeichen"
STATUS_INVALID = "ungueltiger_sollwert"
STATUS_WRITE_ERROR = "schreibfehler"
CONTROL_STATES = (
    STATUS_HEMS,
    STATUS_MANUAL,
    STATUS_NO_HEARTBEAT,
    STATUS_INVALID,
    STATUS_WRITE_ERROR,
)

_INVALID_STATES = frozenset({"unknown", "unavailable", ""})


@dataclass(frozen=True, slots=True)
class Target:
    """Wirksamer Sollwert. `current_a == 0` heißt Laden unterbinden."""

    current_a: int
    phases: int | None  # None = Phasenmodus nicht anfassen
    source: str
    problem: str | None = None


def parse_whole_number(state: State | None) -> int | None:
    """HA-State als ganze Zahl; `None` bei fehlend, unbekannt, nicht endlich, nicht ganzzahlig."""
    if state is None or state.state in _INVALID_STATES:
        return None
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value != round(value):
        return None
    return int(round(value))


def _state_text(state: State | None) -> str:
    return "fehlt" if state is None else state.state


class WallboxControl:
    """Bildet den wirksamen Sollwert und schreibt ihn an die Wallbox."""

    def __init__(
        self,
        coordinator: WallboxCoordinator,
        *,
        hems_entity_prefix: str | None,
        phase_mode: str,
        keepalive: timedelta,
        timeout_factor: float,
    ) -> None:
        self._coordinator = coordinator
        self._hass: HomeAssistant = coordinator.hass
        self._prefix = hems_entity_prefix or None
        self._phase_mode = phase_mode
        self._keepalive = keepalive
        self._current_entity = (
            f"input_number.ems_{self._prefix}_anforderung_leistung_a" if self._prefix else None
        )
        self._phase_entity = (
            f"input_number.ems_{self._prefix}_anzahl_phase" if self._prefix else None
        )
        self._heartbeat = HemsHeartbeat(timeout_factor)
        self._heartbeat_fresh = False

        # Betriebsart: nach jedem Start HEMS, sofern angebunden (Vertrag: Standard an).
        self._hems_enabled = self._prefix is not None
        self._manual_current_a = 0
        self._manual_phases = 1

        self._written_phases: int | None = None
        self._last_target: Target | None = None
        self._last_hems_target: Target | None = None
        self._last_hems_phases: int | None = None
        self._write_ok = True
        self._status = STATUS_HEMS if self._hems_enabled else STATUS_MANUAL

        self._running = False
        self._dirty = False
        self._unsubs: list[Callable[[], None]] = []

    # ------------------------------------------------------------------ öffentliche Sicht

    @property
    def has_hems(self) -> bool:
        return self._prefix is not None

    @property
    def phase_switching(self) -> bool:
        return self._phase_mode == PHASE_MODE_AUTOMATIC

    @property
    def hems_enabled(self) -> bool:
        return self._hems_enabled

    @property
    def heartbeat_fresh(self) -> bool:
        return self._heartbeat_fresh

    @property
    def write_ok(self) -> bool:
        return self._write_ok

    @property
    def status(self) -> str:
        return self._status

    @property
    def manual_current_a(self) -> int:
        return self._manual_current_a

    @property
    def manual_phases(self) -> int:
        return self._manual_phases

    @property
    def last_hems_current_a(self) -> int | None:
        """Zuletzt erfolgreich gesendeter HEMS-Strom; `None` vor Erfolg und nach Schreibfehler."""
        if not self._write_ok or self._last_hems_target is None:
            return None
        return self._last_hems_target.current_a

    @property
    def last_hems_phases(self) -> int | None:
        """Zuletzt erfolgreich angeforderte Phasenzahl im HEMS-Betrieb."""
        if not self._write_ok or self._last_hems_target is None:
            return None
        return self._last_hems_phases

    @property
    def max_current_a(self) -> int:
        data = self._coordinator.data
        if data is not None and data.max_current_a:
            return data.max_current_a
        return FALLBACK_MAX_CURRENT_A

    @property
    def min_current_a(self) -> int:
        return self._coordinator.adapter.min_current_a

    # ------------------------------------------------------------------ Lebenszyklus

    async def async_setup(self) -> None:
        if self._prefix:
            status = self._hass.states.get(STATUS_ENTITY_ID)
            self._heartbeat.observe(
                None if status is None else status.state,
                None if status is None else status.attributes,
            )
            self._unsubs.append(
                async_track_state_change_event(
                    self._hass,
                    [self._current_entity, self._phase_entity],
                    self._async_handle_helper,
                )
            )
            self._unsubs.append(
                async_track_state_change_event(
                    self._hass, [STATUS_ENTITY_ID], self._async_handle_heartbeat
                )
            )
            self._unsubs.append(
                async_track_time_interval(
                    self._hass, self._async_handle_heartbeat_check, HEARTBEAT_CHECK_INTERVAL
                )
            )
        self._unsubs.append(
            async_track_time_interval(self._hass, self._async_handle_keepalive, self._keepalive)
        )
        await self.async_apply()

    def async_unload(self) -> None:
        while self._unsubs:
            self._unsubs.pop()()

    # ------------------------------------------------------------------ Bedienung

    async def async_set_hems_enabled(self, enabled: bool) -> None:
        self._hems_enabled = enabled and self._prefix is not None
        await self.async_apply()

    async def async_set_manual_current(self, current_a: int) -> None:
        self._manual_current_a = current_a
        if not self._hems_enabled:
            await self.async_apply()
        else:
            self._coordinator.async_update_listeners()

    async def async_set_manual_phases(self, phases: int) -> None:
        self._manual_phases = phases
        if not self._hems_enabled:
            await self.async_apply()
        else:
            self._coordinator.async_update_listeners()

    def request_apply(self) -> None:
        """Synchronisierung anstoßen, ohne auf sie zu warten."""
        self._hass.async_create_task(self.async_apply())

    # ------------------------------------------------------------------ Sollwert

    def effective_target(self) -> Target:
        """Wirksamer Sollwert gemäß Betriebsart, Lebenszeichen und Validierung."""
        if not self._hems_enabled:
            phases = self._manual_phases if self.phase_switching else None
            return Target(self._manual_current_a, phases if self._manual_current_a else None,
                          SOURCE_MANUAL)
        if not self._heartbeat.is_fresh():
            return Target(0, None, SOURCE_HEMS, STATUS_NO_HEARTBEAT)

        current = parse_whole_number(self._hass.states.get(self._current_entity))
        if current is None or current < 0 or 0 < current < self.min_current_a or (
            current > self.max_current_a
        ):
            return Target(0, None, SOURCE_HEMS, STATUS_INVALID)
        phases: int | None = None
        if self.phase_switching:
            phases = parse_whole_number(self._hass.states.get(self._phase_entity))
            if phases not in (1, 3):
                return Target(0, None, SOURCE_HEMS, STATUS_INVALID)
        if current == 0:
            return Target(0, None, SOURCE_HEMS)
        return Target(current, phases, SOURCE_HEMS)

    # ------------------------------------------------------------------ Ausführung

    async def async_apply(self) -> None:
        """Den wirksamen Sollwert schreiben. Läuft bereits eine Folge, beginnt sie danach neu."""
        self._dirty = True
        if self._running:
            return
        self._running = True
        try:
            while self._dirty:
                self._dirty = False
                await self._async_execute(self.effective_target())
        finally:
            self._running = False

    async def _async_execute(self, target: Target) -> None:
        adapter = self._coordinator.adapter
        steps: list[tuple[str, int]] = []
        if target.current_a == 0:
            steps.append(("allow", 0))
        else:
            if target.phases is not None and target.phases != self._written_phases:
                steps.append(("phases", target.phases))
            steps += [("current", target.current_a), ("allow", 1)]

        try:
            for kind, value in steps:
                positive = not (kind == "allow" and value == 0)
                if positive and self.effective_target() != target:
                    # Neuerer Sollwert (insbesondere Stopp): Rest verwerfen, neu beginnen.
                    self._dirty = True
                    return
                if kind == "phases":
                    await adapter.set_phases(value)
                    self._written_phases = value
                elif kind == "current":
                    await adapter.set_current(value)
                else:
                    await adapter.allow_charging(bool(value))
        except WallboxAdapterError as exc:
            if self._write_ok:
                _LOGGER.error("Wallbox: Sollwert konnte nicht gesetzt werden: %s", exc)
            else:
                _LOGGER.debug("Wallbox: Sollwert weiterhin nicht gesetzt: %s", exc)
            self._write_ok = False
            self._status = STATUS_WRITE_ERROR
            self._coordinator.async_update_listeners()
            return

        if not self._write_ok:
            _LOGGER.warning("Wallbox: Sollwert wird wieder gesetzt.")
        if target.problem == STATUS_INVALID and self._status != STATUS_INVALID:
            # Nur beim Eintritt — das Neuschreiben im Takt soll das Log nicht fluten.
            _LOGGER.warning(
                "Wallbox: ungültiger HEMS-Sollwert (Strom %s, Phasen %s) — Laden unterbunden.",
                _state_text(self._hass.states.get(self._current_entity)),
                _state_text(self._hass.states.get(self._phase_entity)),
            )
        self._write_ok = True
        self._last_target = target
        if target.source == SOURCE_HEMS:
            self._last_hems_target = target
            if target.phases is not None:
                self._last_hems_phases = target.phases
            self._status = target.problem or STATUS_HEMS
        else:
            self._status = STATUS_MANUAL
        self._coordinator.async_update_listeners()

    # ------------------------------------------------------------------ Ereignisse

    async def _async_handle_helper(self, _event: Event) -> None:
        if self._hems_enabled:
            await self.async_apply()

    async def _async_handle_keepalive(self, _now: datetime) -> None:
        await self.async_apply()

    async def _async_handle_heartbeat(self, event: Event) -> None:
        new_state = event.data.get("new_state")
        self._heartbeat.observe(
            None if new_state is None else new_state.state,
            None if new_state is None else new_state.attributes,
        )
        await self._async_check_heartbeat()

    async def _async_handle_heartbeat_check(self, _now: datetime) -> None:
        await self._async_check_heartbeat()

    async def _async_check_heartbeat(self) -> None:
        fresh = self._heartbeat.is_fresh()
        if fresh == self._heartbeat_fresh:
            return
        self._heartbeat_fresh = fresh
        if fresh:
            _LOGGER.info("Wallbox: HEMS-Lebenszeichen wieder da (%s).", self._prefix)
        else:
            _LOGGER.warning(
                "Wallbox: HEMS-Lebenszeichen ausgeblieben (%s) — Laden wird gestoppt.",
                self._prefix,
            )
        self._coordinator.async_update_listeners()
        if self._hems_enabled:
            await self.async_apply()
