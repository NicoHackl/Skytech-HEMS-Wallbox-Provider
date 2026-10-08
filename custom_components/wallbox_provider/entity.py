"""Gemeinsame Basis aller Entities: Geräteinfo und Entity-IDs nach dem Vertrag.

Die Entity-ID wird ausdrücklich als `<plattform>.<provider_prefix>_<key>` vorgeschlagen, damit
sie den Namen im Vertrag entspricht (z. B. `binary_sensor.<prefix>_laedt` statt der aus dem
übersetzten Namen abgeleiteten Form). `<provider_prefix>` ist der slugifizierte Anzeigename.
Vergebene oder umbenannte IDs verwaltet Home Assistant; die Zuordnung pflegt der Anwender.
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_MANUFACTURER, DOMAIN, MANUFACTURER_NAMES
from .coordinator import WallboxConfigEntry, WallboxCoordinator
from .hems_bridge import WallboxControl


def provider_prefix(entry: WallboxConfigEntry) -> str:
    return slugify(entry.title)


class WallboxEntity(CoordinatorEntity[WallboxCoordinator]):
    """Basis mit Geräteinfo, Unique ID und vertragsgemäßer Entity-ID."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: WallboxCoordinator, entry: WallboxConfigEntry, platform: str, key: str
    ) -> None:
        super().__init__(coordinator)
        device_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"{platform}.{provider_prefix(entry)}_{key}"
        manufacturer = entry.data[CONF_MANUFACTURER]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=entry.title,
            manufacturer=MANUFACTURER_NAMES.get(manufacturer, manufacturer),
        )

    @property
    def control(self) -> WallboxControl:
        # Wird in __init__.py vor dem Laden der Platforms gesetzt.
        assert self.coordinator.control is not None
        return self.coordinator.control
