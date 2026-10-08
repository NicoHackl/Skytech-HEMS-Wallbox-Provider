"""switch.py — „HEMS Steuerung": an = Betriebsart HEMS, aus = manuell (D-005).

Nur mit HEMS-Präfix angelegt. Standard nach jedem Neustart: an. Auch die HEMS-Notabschaltung
übersteuert „aus" nicht (Vertrag, bekannte Grenze).
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
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
    if coordinator.control is not None and coordinator.control.has_hems:
        async_add_entities([WallboxHemsSwitch(coordinator, entry)])


class WallboxHemsSwitch(WallboxEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: WallboxCoordinator, entry: WallboxConfigEntry) -> None:
        super().__init__(coordinator, entry, "switch", "hems_steuerung_aktiv")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.control.hems_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.control.async_set_hems_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.control.async_set_hems_enabled(False)
        self.async_write_ha_state()
