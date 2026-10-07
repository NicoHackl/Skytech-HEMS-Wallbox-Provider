"""Skytech HEMS Wallbox Provider — Setup und Unload der Integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .adapters.base import WallboxAdapter
from .adapters.goe_modbus import GoeModbusAdapter
from .const import (
    CONF_HEMS_ENTITY_PREFIX,
    CONF_HEMS_TIMEOUT_FACTOR,
    CONF_KEEPALIVE,
    CONF_MANUFACTURER,
    CONF_PHASE_MODE,
    CONF_PROTOCOL,
    CONF_UNIT_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_KEEPALIVE_SECONDS,
    DEFAULT_UNIT_ID,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    MANUFACTURER_GOE,
    PHASE_MODE_AUTOMATIC,
    PROTOCOL_GOE_MODBUS,
)
from .coordinator import WallboxConfigEntry, WallboxCoordinator
from .heartbeat import DEFAULT_TIMEOUT_FACTOR
from .hems_bridge import WallboxControl

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: WallboxConfigEntry) -> bool:
    """Adapter bauen, Coordinator starten, Steuerung einrichten, Platforms laden."""
    adapter = build_adapter(entry.data)
    coordinator = WallboxCoordinator(
        hass,
        entry,
        adapter,
        update_interval=timedelta(
            seconds=entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SECONDS)
        ),
    )
    await coordinator.async_config_entry_first_refresh()

    coordinator.control = WallboxControl(
        coordinator,
        hems_entity_prefix=entry.data.get(CONF_HEMS_ENTITY_PREFIX),
        phase_mode=entry.data.get(CONF_PHASE_MODE, PHASE_MODE_AUTOMATIC),
        keepalive=timedelta(
            seconds=entry.options.get(CONF_KEEPALIVE, DEFAULT_KEEPALIVE_SECONDS)
        ),
        timeout_factor=entry.options.get(CONF_HEMS_TIMEOUT_FACTOR, DEFAULT_TIMEOUT_FACTOR),
    )
    entry.runtime_data = coordinator
    await coordinator.control.async_setup()

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: WallboxConfigEntry) -> None:
    """Options-Änderung wirkt sofort per Reload."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: WallboxConfigEntry) -> bool:
    """Platforms entladen, Steuerung abmelden, Transport schließen.

    Kein Abschaltbefehl beim Entladen: die Wallbox behält den zuletzt gesetzten Zustand
    (Vertrag, bekannte Grenze Verbindungsverlust).
    """
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator = entry.runtime_data
        if coordinator.control is not None:
            coordinator.control.async_unload()
        await coordinator.adapter.close()
    return unloaded


def build_adapter(data: dict) -> WallboxAdapter:
    """Einzige Stelle, die Hersteller/Protokoll auf eine Adapter-Klasse abbildet."""
    manufacturer = data[CONF_MANUFACTURER]
    protocol = data[CONF_PROTOCOL]
    if manufacturer == MANUFACTURER_GOE and protocol == PROTOCOL_GOE_MODBUS:
        return GoeModbusAdapter(
            data[CONF_HOST], data[CONF_PORT], data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
        )
    raise ValueError(f"Unbekannter Hersteller/Protokoll: {manufacturer}/{protocol}")
