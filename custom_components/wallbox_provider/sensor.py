"""sensor.py — Mess-, Status- und HEMS-Diagnose-Sensoren (Vertrag, Provider → HEMS).

Messsensoren hängen am Poll: schlägt er fehl oder fehlt ein Wert, sind sie nicht verfügbar —
nie `0`. Die HEMS-Sollsensoren hängen an der Steuerung, nicht am Poll: sie zeigen nur einen
erfolgreich gesendeten Wert und sind vor dem ersten Erfolg und nach einem Schreibfehler nicht
verfügbar.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WallboxConfigEntry, WallboxCoordinator
from .entity import WallboxEntity
from .hems_bridge import CONTROL_STATES, WallboxControl
from .models import FAULTS, VEHICLE_STATES, WallboxState


@dataclass(frozen=True, kw_only=True)
class MeasureDescription(SensorEntityDescription):
    value_fn: Callable[[WallboxState], float | int | str | None]


def _voltage(key: str, fn: Callable[[WallboxState], float | None]) -> MeasureDescription:
    return MeasureDescription(
        key=key,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=fn,
    )


def _current(key: str, fn: Callable[[WallboxState], float | None]) -> MeasureDescription:
    return MeasureDescription(
        key=key,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=fn,
    )


MEASURES: tuple[MeasureDescription, ...] = (
    MeasureDescription(
        key="istleistung",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda s: s.charging_power_w,
    ),
    _voltage("spannung_l1", lambda s: s.voltage_l1_v),
    _voltage("spannung_l2", lambda s: s.voltage_l2_v),
    _voltage("spannung_l3", lambda s: s.voltage_l3_v),
    _current("ladestrom_l1", lambda s: s.current_l1_a),
    _current("ladestrom_l2", lambda s: s.current_l2_a),
    _current("ladestrom_l3", lambda s: s.current_l3_a),
    MeasureDescription(
        key="aktuelle_phasenanzahl",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.active_phase_count,
    ),
    MeasureDescription(
        key="wallbox_status",
        device_class=SensorDeviceClass.ENUM,
        options=list(VEHICLE_STATES),
        value_fn=lambda s: s.vehicle_state,
    ),
    MeasureDescription(
        key="fehler",
        device_class=SensorDeviceClass.ENUM,
        options=list(FAULTS),
        value_fn=lambda s: s.fault,
    ),
    MeasureDescription(
        key="ladeenergie_sitzung",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=0,
        value_fn=lambda s: s.session_energy_wh,
    ),
    MeasureDescription(
        key="ladeenergie_gesamt",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        value_fn=lambda s: s.total_energy_wh,
    ),
)


@dataclass(frozen=True, kw_only=True)
class ControlDescription(SensorEntityDescription):
    value_fn: Callable[[WallboxControl], int | str | None]


HEMS_CURRENT = ControlDescription(
    key="hems_soll_ladestrom",
    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    device_class=SensorDeviceClass.CURRENT,
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=lambda c: c.last_hems_current_a,
)
HEMS_PHASES = ControlDescription(
    key="hems_soll_phasenanzahl",
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=lambda c: c.last_hems_phases,
)
CONTROL_STATUS = ControlDescription(
    key="steuerung",
    device_class=SensorDeviceClass.ENUM,
    options=list(CONTROL_STATES),
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=lambda c: c.status,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WallboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        WallboxMeasureSensor(coordinator, entry, d) for d in MEASURES
    ]
    entities.append(WallboxControlSensor(coordinator, entry, CONTROL_STATUS))
    control = coordinator.control
    assert control is not None
    if control.has_hems:
        entities.append(WallboxControlSensor(coordinator, entry, HEMS_CURRENT))
        if control.phase_switching:
            entities.append(WallboxControlSensor(coordinator, entry, HEMS_PHASES))
    async_add_entities(entities)


class WallboxMeasureSensor(WallboxEntity, SensorEntity):
    entity_description: MeasureDescription

    def __init__(
        self, coordinator: WallboxCoordinator, entry: WallboxConfigEntry, d: MeasureDescription
    ) -> None:
        super().__init__(coordinator, entry, "sensor", d.key)
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
    def native_value(self) -> float | int | str | None:
        data = self.coordinator.data
        return None if data is None else self.entity_description.value_fn(data)


class WallboxControlSensor(WallboxEntity, SensorEntity):
    entity_description: ControlDescription
    _attr_assumed_state = True

    def __init__(
        self, coordinator: WallboxCoordinator, entry: WallboxConfigEntry, d: ControlDescription
    ) -> None:
        super().__init__(coordinator, entry, "sensor", d.key)
        self.entity_description = d

    @property
    def available(self) -> bool:
        return self.entity_description.value_fn(self.control) is not None

    @property
    def native_value(self) -> int | str | None:
        return self.entity_description.value_fn(self.control)
