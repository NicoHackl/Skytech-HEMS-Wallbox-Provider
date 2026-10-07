"""Config- und Options-Flow."""

from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.wallbox_provider.adapters.base import (
    WallboxAdapterError,
    WallboxFirmwareError,
)
from custom_components.wallbox_provider.const import (
    CONF_HEMS_TIMEOUT_FACTOR,
    CONF_KEEPALIVE,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)
from tests.conftest import FakeAdapter, setup_entry

_INPUT = {
    "display_name": "go-e Garage",
    "host": "192.0.2.10",
    "port": 502,
    "unit_id": 1,
    "hems_entity_prefix": "wallbox",
    "phase_mode": "automatisch",
    "update_interval_seconds": 5,
}


def _patch(monkeypatch: pytest.MonkeyPatch, adapter: FakeAdapter) -> None:
    monkeypatch.setattr(
        "custom_components.wallbox_provider.config_flow.build_adapter", lambda data: adapter
    )
    monkeypatch.setattr("custom_components.wallbox_provider.build_adapter", lambda data: adapter)


async def _start(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_einrichtung_mit_seriennummer_als_unique_id(
    hass: HomeAssistant, monkeypatch
) -> None:
    _patch(monkeypatch, FakeAdapter())
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], _INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "go-e Garage"
    assert result["result"].unique_id == "123456"
    assert result["data"]["hems_entity_prefix"] == "wallbox"
    assert result["data"]["phase_mode"] == "automatisch"


async def test_doppelte_einrichtung_abgelehnt(hass: HomeAssistant, monkeypatch) -> None:
    await setup_entry(hass, monkeypatch)
    _patch(monkeypatch, FakeAdapter())
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], _INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("error", "key"),
    [(WallboxAdapterError("x"), "cannot_connect"),
     (WallboxFirmwareError("x"), "unsupported_firmware")],
)
async def test_fehler_beim_verbindungstest(
    hass: HomeAssistant, monkeypatch, error, key
) -> None:
    adapter = FakeAdapter()

    async def fail():
        raise error

    adapter.identify = fail
    _patch(monkeypatch, adapter)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], _INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": key}


async def test_leeres_hems_praefix_wird_none(hass: HomeAssistant, monkeypatch) -> None:
    _patch(monkeypatch, FakeAdapter())
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**_INPUT, "hems_entity_prefix": "  "}
    )
    assert result["data"]["hems_entity_prefix"] is None


async def test_options_flow(hass: HomeAssistant, monkeypatch) -> None:
    entry, _adapter = await setup_entry(hass, monkeypatch)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    defaults = result["data_schema"]({})
    assert defaults == {CONF_UPDATE_INTERVAL: 5, CONF_KEEPALIVE: 30, CONF_HEMS_TIMEOUT_FACTOR: 3}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_UPDATE_INTERVAL: 5, CONF_KEEPALIVE: 2, CONF_HEMS_TIMEOUT_FACTOR: 3},
    )
    assert result["errors"] == {CONF_KEEPALIVE: "invalid_keepalive"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_UPDATE_INTERVAL: 5, CONF_KEEPALIVE: 60, CONF_HEMS_TIMEOUT_FACTOR: 4},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options[CONF_KEEPALIVE] == 60


async def test_options_ohne_hems_ohne_frist(hass: HomeAssistant, monkeypatch) -> None:
    entry, _adapter = await setup_entry(hass, monkeypatch, hems_entity_prefix=None)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert CONF_HEMS_TIMEOUT_FACTOR not in result["data_schema"]({})
