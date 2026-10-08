"""config_flow.py — Verbindungsdaten, HEMS-Anbindung, Phasenbetrieb, Verbindungstest.

Die Seriennummer der Wallbox ist die Unique ID des Entries (nicht IP oder Anzeigename); eine
zweite Einrichtung desselben Geräts wird abgelehnt. Firmware ohne die benötigten Modbus-Register
oder mit bekanntem Byte-Reihenfolgefehler wird beim Einrichten abgewiesen.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from . import build_adapter
from .adapters.base import WallboxAdapterError, WallboxFirmwareError
from .const import (
    CONF_DISPLAY_NAME,
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
    DOMAIN,
    GOE_MODBUS_DEFAULT_PORT,
    MANUFACTURER_GOE,
    MAX_KEEPALIVE_SECONDS,
    MAX_UPDATE_INTERVAL_SECONDS,
    MIN_KEEPALIVE_SECONDS,
    MIN_UPDATE_INTERVAL_SECONDS,
    PHASE_MODE_AUTOMATIC,
    PHASE_MODES,
    PROTOCOL_GOE_MODBUS,
)
from .heartbeat import DEFAULT_TIMEOUT_FACTOR, MAX_TIMEOUT_FACTOR, MIN_TIMEOUT_FACTOR

_LOGGER = logging.getLogger(__name__)

_PHASE_MODE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=list(PHASE_MODES),
        mode=SelectSelectorMode.DROPDOWN,
        translation_key="phase_mode",
    )
)


def _check_range(
    user_input: dict[str, Any], key: str, default: int, low: int, high: int,
    errors: dict[str, str], error: str,
) -> int:
    value = user_input.get(key, default)
    if not low <= value <= high:
        errors[key] = error
    return value


class WallboxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ein Schritt: go-e über Modbus TCP (einziger Adapter in V1)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            update_interval = _check_range(
                user_input, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SECONDS,
                MIN_UPDATE_INTERVAL_SECONDS, MAX_UPDATE_INTERVAL_SECONDS,
                errors, "invalid_update_interval",
            )
            data = {
                CONF_MANUFACTURER: MANUFACTURER_GOE,
                CONF_PROTOCOL: PROTOCOL_GOE_MODBUS,
                CONF_HOST: user_input[CONF_HOST].strip(),
                CONF_PORT: user_input[CONF_PORT],
                CONF_UNIT_ID: user_input.get(CONF_UNIT_ID, DEFAULT_UNIT_ID),
                CONF_HEMS_ENTITY_PREFIX: (user_input.get(CONF_HEMS_ENTITY_PREFIX) or "").strip()
                or None,
                CONF_PHASE_MODE: user_input.get(CONF_PHASE_MODE, PHASE_MODE_AUTOMATIC),
            }
            if not errors:
                serial = await self._async_identify(data, errors)
                if serial is not None:
                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_configured()
                    title = (user_input.get(CONF_DISPLAY_NAME) or "").strip() or (
                        f"go-e {serial}"
                    )
                    return self.async_create_entry(
                        title=title,
                        data=data,
                        options={CONF_UPDATE_INTERVAL: update_interval},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_DISPLAY_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=GOE_MODBUS_DEFAULT_PORT): int,
                    vol.Optional(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
                    vol.Optional(CONF_HEMS_ENTITY_PREFIX): str,
                    vol.Required(
                        CONF_PHASE_MODE, default=PHASE_MODE_AUTOMATIC
                    ): _PHASE_MODE_SELECTOR,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL_SECONDS
                    ): int,
                }
            ),
            errors=errors,
        )

    async def _async_identify(self, data: dict[str, Any], errors: dict[str, str]) -> str | None:
        adapter = build_adapter(data)
        try:
            await adapter.connect()
            serial, firmware = await adapter.identify()
        except WallboxFirmwareError as exc:
            _LOGGER.warning("Wallbox %s nicht unterstützt: %s", data[CONF_HOST], exc)
            errors["base"] = "unsupported_firmware"
            return None
        except WallboxAdapterError as exc:
            _LOGGER.debug("Verbindungstest zu %s fehlgeschlagen: %s", data[CONF_HOST], exc)
            errors["base"] = "cannot_connect"
            return None
        finally:
            await adapter.close()
        _LOGGER.info("Wallbox %s erkannt, Firmware %s", serial, firmware)
        return serial

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> WallboxOptionsFlow:
        return WallboxOptionsFlow()


class WallboxOptionsFlow(OptionsFlow):
    """Abfrageintervall, Neuschreib-Takt und — mit HEMS-Anbindung — Frist-Faktor."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        options = self.config_entry.options
        has_hems = bool(self.config_entry.data.get(CONF_HEMS_ENTITY_PREFIX))

        if user_input is not None:
            data: dict[str, Any] = {
                CONF_UPDATE_INTERVAL: _check_range(
                    user_input, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SECONDS,
                    MIN_UPDATE_INTERVAL_SECONDS, MAX_UPDATE_INTERVAL_SECONDS,
                    errors, "invalid_update_interval",
                ),
                CONF_KEEPALIVE: _check_range(
                    user_input, CONF_KEEPALIVE, DEFAULT_KEEPALIVE_SECONDS,
                    MIN_KEEPALIVE_SECONDS, MAX_KEEPALIVE_SECONDS, errors, "invalid_keepalive",
                ),
            }
            if has_hems:
                data[CONF_HEMS_TIMEOUT_FACTOR] = _check_range(
                    user_input, CONF_HEMS_TIMEOUT_FACTOR, DEFAULT_TIMEOUT_FACTOR,
                    MIN_TIMEOUT_FACTOR, MAX_TIMEOUT_FACTOR, errors, "invalid_hems_timeout_factor",
                )
            if not errors:
                return self.async_create_entry(title="", data=data)

        schema: dict[Any, Any] = {
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SECONDS),
            ): int,
            vol.Optional(
                CONF_KEEPALIVE, default=options.get(CONF_KEEPALIVE, DEFAULT_KEEPALIVE_SECONDS)
            ): int,
        }
        if has_hems:
            schema[
                vol.Optional(
                    CONF_HEMS_TIMEOUT_FACTOR,
                    default=options.get(CONF_HEMS_TIMEOUT_FACTOR, DEFAULT_TIMEOUT_FACTOR),
                )
            ] = int
        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema), errors=errors)
