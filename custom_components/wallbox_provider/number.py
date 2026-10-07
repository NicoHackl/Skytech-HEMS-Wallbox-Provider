"""number.py — manueller Ladestrom für die Betriebsart „manuell" (D-005).

`0` heißt Laden unterbinden. Werte zwischen 0 und dem Gerätemindeststrom werden abgelehnt, nie
gerundet. Standard beim Anlegen und nach jedem Neustart: 0.
"""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import WallboxConfigEntry, WallboxCoordinator
from .entity import WallboxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WallboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([WallboxManualCurrent(entry.runtime_data, entry)])


class WallboxManualCurrent(WallboxEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(self, coordinator: WallboxCoordinator, entry: WallboxConfigEntry) -> None:
        super().__init__(coordinator, entry, "number", "manueller_ladestrom")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_max_value(self) -> float:
        return float(self.control.max_current_a)

    @property
    def native_value(self) -> float:
        return float(self.control.manual_current_a)

    async def async_set_native_value(self, value: float) -> None:
        current = int(value)
        if current != value or (0 < current < self.control.min_current_a):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_manual_current",
                translation_placeholders={"minimum": str(self.control.min_current_a)},
            )
        await self.control.async_set_manual_current(current)
        self.async_write_ha_state()
