"""Gemeinsame Test-Helfer: Fake-Adapter, Entry-Fabrik, simulierter HEMS-Zyklus."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wallbox_provider.adapters.base import WallboxAdapterError
from custom_components.wallbox_provider.const import (
    CONF_HEMS_ENTITY_PREFIX,
    CONF_MANUFACTURER,
    CONF_PHASE_MODE,
    CONF_PROTOCOL,
    CONF_UNIT_ID,
    DOMAIN,
    MANUFACTURER_GOE,
    PHASE_MODE_AUTOMATIC,
    PROTOCOL_GOE_MODBUS,
)
from custom_components.wallbox_provider.models import WallboxState

PREFIX = "wallbox"
CURRENT_ENTITY = f"input_number.ems_{PREFIX}_anforderung_leistung_a"
PHASE_ENTITY = f"input_number.ems_{PREFIX}_anzahl_phase"
STATUS_ENTITY = "sensor.skytech_hems_status"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


def make_state(**over) -> WallboxState:
    base = dict(
        charging_power_w=0.0,
        voltage_l1_v=230.0,
        voltage_l2_v=231.0,
        voltage_l3_v=229.0,
        current_l1_a=0.0,
        current_l2_a=0.0,
        current_l3_a=0.0,
        active_phase_count=0,
        vehicle_state="wartet_auf_fahrzeug",
        vehicle_connected=True,
        is_charging=False,
        fault="kein_fehler",
        session_energy_wh=0.0,
        total_energy_wh=1000.0,
        max_current_a=16,
        available=True,
        last_update=datetime.now(UTC),
    )
    base.update(over)
    return WallboxState(**base)


class FakeAdapter:
    """Zeichnet Befehle auf. `fail_writes` lässt Schreibvorgänge scheitern, `fail_reads` Polls."""

    min_current_a = 6

    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.state = make_state()
        self.fail_writes = False
        self.fail_reads = False
        self.serial = "123456"
        self.firmware = "56.2"
        self.on_write = None  # optionaler Rückruf nach jedem erfolgreichen Schreibvorgang

    async def connect(self) -> None:
        return None

    async def identify(self) -> tuple[str, str]:
        return self.serial, self.firmware

    async def read(self) -> WallboxState:
        if self.fail_reads:
            raise WallboxAdapterError("Timeout")
        return self.state

    async def _record(self, kind: str, value: object) -> None:
        if self.fail_writes:
            raise WallboxAdapterError("Schreiben fehlgeschlagen")
        self.calls.append((kind, value))
        if self.on_write is not None:
            await self.on_write(kind, value)

    async def set_current(self, current_a: int) -> None:
        await self._record("current", current_a)

    async def set_phases(self, phases: int) -> None:
        await self._record("phases", phases)

    async def allow_charging(self, allowed: bool) -> None:
        await self._record("allow", allowed)

    async def close(self) -> None:
        return None


def make_entry(
    *, hems_entity_prefix: str | None = PREFIX, phase_mode: str = PHASE_MODE_AUTOMATIC,
    title: str = "go-e Garage", options: dict | None = None,
) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title=title,
        unique_id="123456",
        data={
            CONF_MANUFACTURER: MANUFACTURER_GOE,
            CONF_PROTOCOL: PROTOCOL_GOE_MODBUS,
            CONF_HOST: "192.0.2.10",
            CONF_PORT: 502,
            CONF_UNIT_ID: 1,
            CONF_HEMS_ENTITY_PREFIX: hems_entity_prefix,
            CONF_PHASE_MODE: phase_mode,
        },
        options=options or {},
    )


async def setup_entry(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, **kwargs
) -> tuple[MockConfigEntry, FakeAdapter]:
    adapter = FakeAdapter()
    monkeypatch.setattr(
        "custom_components.wallbox_provider.build_adapter", lambda data: adapter
    )
    entry = make_entry(**kwargs)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, adapter


_counter = 0


async def hems_zyklus(hass: HomeAssistant, interval_s: float = 30) -> None:
    """Einen SkytechHEMS-Zyklus simulieren: das Lebenszeichen ändert seinen Zähler."""
    global _counter
    _counter += 1
    hass.states.async_set(
        STATUS_ENTITY, str(_counter), {"zyklus_zaehler": _counter, "zyklus_intervall_s": interval_s}
    )
    await hass.async_block_till_done()


async def set_hems(hass: HomeAssistant, current: str | None, phases: str | None = "1") -> None:
    """HEMS-Reihenfolge: Phase vor Strom."""
    if phases is not None:
        hass.states.async_set(PHASE_ENTITY, phases)
        await hass.async_block_till_done()
    if current is not None:
        hass.states.async_set(CURRENT_ENTITY, current)
        await hass.async_block_till_done()


def entity_ids_by_key(hass: HomeAssistant, entry: MockConfigEntry) -> dict[str, str]:
    registry = er.async_get(hass)
    result = {}
    for item in er.async_entries_for_config_entry(registry, entry.entry_id):
        result[item.unique_id.split("_", 1)[1]] = item.entity_id
    return result
