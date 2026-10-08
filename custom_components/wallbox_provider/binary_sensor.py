"""binary_sensor.py — Fahrzeug verbunden, lädt, HEMS-Lebenszeichen."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WallboxConfigEntry, WallboxCoordinator
from .entity import WallboxEntity
from .models import WallboxState


@dataclass(frozen=True, kw_only=True)
class StateDescription(BinarySensorEntityDescription):
    value_fn: Callable[[WallboxState], bool | None]


STATES: tuple[StateDescription, ...] = (
    StateDescription(
        key="fahrzeug_verbunden",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda s: s.vehicle_connected,
    ),
    StateDescription(
        key="laedt",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda s: s.is_charging,
    ),
)

HEARTBEAT = BinarySensorEntityDescription(
    key="hems_lebenszeichen",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WallboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        WallboxStateSensor(coordinator, entry, d) for d in STATES
    ]
    if coordinator.control is not None and coordinator.control.has_hems:
        entities.append(WallboxHeartbeatSensor(coordinator, entry))
    async_add_entities(entities)


class WallboxStateSensor(WallboxEntity, BinarySensorEntity):
    entity_description: StateDescription

    def __init__(
        self, coordinator: WallboxCoordinator, entry: WallboxConfigEntry, d: StateDescription
    ) -> None:
        super().__init__(coordinator, entry, "binary_sensor", d.key)
        self.entity_description = d

    @property
    def available(self) -> bool:
        data = self.coordinator.data
        return (
            super().available
            and data is not None
            and data.available
            and self.entity_description.value_fn(data) is not None
        )

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        return None if data is None else self.entity_description.value_fn(data)


class WallboxHeartbeatSensor(WallboxEntity, BinarySensorEntity):
    """An, solange das HEMS-Lebenszeichen frisch ist (D-004). Unabhängig vom Poll."""

    def __init__(self, coordinator: WallboxCoordinator, entry: WallboxConfigEntry) -> None:
        super().__init__(coordinator, entry, "binary_sensor", HEARTBEAT.key)
        self.entity_description = HEARTBEAT

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.control.heartbeat_fresh
