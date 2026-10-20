"""interface.py — sensor.wallbox_provider_schnittstelle, die eine Schnittstellen-Entität (D-007).

Grundsatz der Skytech-Projekte: Jede Einheit veröffentlicht genau eine
`sensor.<einheit>_schnittstelle` mit allen Informationen für die anderen Teilnehmer
(Vertrag HEMS ↔ Wallbox-Provider 2.1). Für diese Integration ist das **ein** Sensor über alle
Wallboxen mit HEMS-Anbindung:

- State: die `hems_entity_prefix` dieser Einträge, durch Komma getrennt.
- Je Wallbox `<prefix>_freigabe` (Bool) und `<prefix>_sperrgrund` (Text oder `None`).

Gesperrt (vom User festgelegt, 20.10.2026): nicht erreichbar (`nicht_erreichbar`), Gerätefehler
(Fehlerart, z. B. `fehlerstrom`) und kein Fahrzeug verbunden (`kein_fahrzeug`). Die Betriebsart
manuell sperrt nicht. Ein unbekannter Wert (`None`) ist keine Sperre. SkytechHEMS nimmt eine
gesperrte Wallbox aus der Verteilung und schreibt 0 A.

Weil der Sensor über alle Config-Entries geht, ist er keine Registry-Entität, sondern wird per
`hass.states.async_set` geschrieben — wie die Schnittstellen von SkytechHEMS und des
Battery-Providers.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import WallboxCoordinator

INTERFACE_ENTITY_ID = "sensor.wallbox_provider_schnittstelle"
# Version der Attributstruktur (Vertrag HEMS ↔ Wallbox-Provider 2.1).
INTERFACE_VERSION = 1
LOCK_UNREACHABLE = "nicht_erreichbar"
LOCK_NO_VEHICLE = "kein_fahrzeug"
_NO_FAULT = "kein_fehler"
_DATA_KEY = "interface"


def get_interface(hass: HomeAssistant) -> WallboxProviderInterface:
    """Die eine Instanz je HA-Installation, bei Bedarf angelegt."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if _DATA_KEY not in domain_data:
        domain_data[_DATA_KEY] = WallboxProviderInterface(hass)
    return domain_data[_DATA_KEY]


class WallboxProviderInterface:
    """Sammelt alle Wallboxen mit HEMS-Anbindung und schreibt den gemeinsamen Sensor."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._members: dict[str, WallboxCoordinator] = {}
        self._unsubs: dict[str, Callable[[], None]] = {}
        self._last_written: tuple[str, dict[str, Any]] | None = None

    @callback
    def register(self, prefix: str, coordinator: WallboxCoordinator) -> None:
        """Eine Wallbox aufnehmen; jede Coordinator-Aktualisierung schreibt den Sensor neu."""
        self.unregister(prefix)
        self._members[prefix] = coordinator
        self._unsubs[prefix] = coordinator.async_add_listener(self.async_publish)
        self.async_publish()

    @callback
    def unregister(self, prefix: str) -> None:
        """Eine Wallbox entfernen (Unload); ohne Wallbox verschwindet der Sensor."""
        unsub = self._unsubs.pop(prefix, None)
        if unsub is not None:
            unsub()
        if self._members.pop(prefix, None) is None:
            return
        if self._members:
            self.async_publish()
        else:
            self._hass.states.async_remove(INTERFACE_ENTITY_ID)
            self._last_written = None

    @callback
    def async_publish(self) -> None:
        """State und Attribute neu berechnen; geschrieben wird nur bei einer Änderung."""
        attributes: dict[str, Any] = {
            "friendly_name": "Wallbox-Provider-Schnittstelle",
            "icon": "mdi:ev-station",
            "schnittstelle_version": INTERFACE_VERSION,
        }
        for prefix, coordinator in self._members.items():
            reasons = lock_reasons(coordinator)
            attributes[f"{prefix}_freigabe"] = not reasons
            attributes[f"{prefix}_sperrgrund"] = ", ".join(reasons) or None
        state = ",".join(self._members)
        if self._last_written == (state, attributes):
            return
        self._last_written = (state, attributes)
        self._hass.states.async_set(INTERFACE_ENTITY_ID, state, attributes)


def lock_reasons(coordinator: WallboxCoordinator) -> list[str]:
    """Sperrgründe einer Wallbox; leer heißt freigegeben."""
    data = coordinator.data
    if not coordinator.last_update_success or data is None or not data.available:
        return [LOCK_UNREACHABLE]
    reasons: list[str] = []
    if data.fault is not None and data.fault != _NO_FAULT:
        reasons.append(data.fault)
    if data.vehicle_connected is False:
        reasons.append(LOCK_NO_VEHICLE)
    return reasons
