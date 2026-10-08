"""select.py — manuelle Phasenzahl für die Betriebsart „manuell" (D-005).

Nur bei Phasenbetrieb `automatisch` angelegt; bei fester Phasenzahl gibt es nichts zu wählen.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WallboxConfigEntry, WallboxCoordinator
from .entity import WallboxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WallboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    if coordinator.control is not None and coordinator.control.phase_switching:
        async_add_entities([WallboxManualPhases(coordinator, entry)])


class WallboxManualPhases(WallboxEntity, SelectEntity):
    _attr_options = ["1", "3"]

    def __init__(self, coordinator: WallboxCoordinator, entry: WallboxConfigEntry) -> None:
        super().__init__(coordinator, entry, "select", "manuelle_phasenanzahl")

    @property
    def available(self) -> bool:
        return True

    @property
    def current_option(self) -> str:
        return str(self.control.manual_phases)

    async def async_select_option(self, option: str) -> None:
        await self.control.async_set_manual_phases(int(option))
        self.async_write_ha_state()
