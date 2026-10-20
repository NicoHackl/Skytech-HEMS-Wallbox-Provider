"""Tests für sensor.wallbox_provider_schnittstelle (interface.py, D-007, Vertrag 2.1)."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.wallbox_provider.interface import INTERFACE_ENTITY_ID
from tests.conftest import PREFIX, make_state, setup_entry


async def _refresh(hass: HomeAssistant, entry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


async def test_freigegeben_im_normalfall(hass: HomeAssistant, monkeypatch) -> None:
    await setup_entry(hass, monkeypatch)
    sensor = hass.states.get(INTERFACE_ENTITY_ID)
    assert sensor.state == PREFIX
    assert sensor.attributes["schnittstelle_version"] == 1
    assert sensor.attributes[f"{PREFIX}_freigabe"] is True
    assert sensor.attributes[f"{PREFIX}_sperrgrund"] is None


@pytest.mark.parametrize(
    ("state", "grund"),
    [
        ({"vehicle_connected": False}, "kein_fahrzeug"),
        ({"fault": "fehlerstrom"}, "fehlerstrom"),
        ({"fault": "uebertemperatur", "vehicle_connected": False},
         "uebertemperatur, kein_fahrzeug"),
        ({"available": False}, "nicht_erreichbar"),
    ],
)
async def test_sperrgruende(hass: HomeAssistant, monkeypatch, state, grund) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    adapter.state = make_state(**state)
    await _refresh(hass, entry)
    attrs = hass.states.get(INTERFACE_ENTITY_ID).attributes
    assert attrs[f"{PREFIX}_freigabe"] is False
    assert attrs[f"{PREFIX}_sperrgrund"] == grund


async def test_pollfehler_ist_nicht_erreichbar(hass: HomeAssistant, monkeypatch) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    adapter.fail_reads = True
    await _refresh(hass, entry)
    attrs = hass.states.get(INTERFACE_ENTITY_ID).attributes
    assert attrs[f"{PREFIX}_freigabe"] is False
    assert attrs[f"{PREFIX}_sperrgrund"] == "nicht_erreichbar"


@pytest.mark.parametrize("over", [{"vehicle_connected": None}, {"fault": None}])
async def test_unbekannt_ist_keine_sperre(hass: HomeAssistant, monkeypatch, over) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    adapter.state = make_state(**over)
    await _refresh(hass, entry)
    assert hass.states.get(INTERFACE_ENTITY_ID).attributes[f"{PREFIX}_freigabe"] is True


async def test_manuelle_betriebsart_sperrt_nicht(hass: HomeAssistant, monkeypatch) -> None:
    entry, _adapter = await setup_entry(hass, monkeypatch)
    await entry.runtime_data.control.async_set_hems_enabled(False)
    await _refresh(hass, entry)
    assert hass.states.get(INTERFACE_ENTITY_ID).attributes[f"{PREFIX}_freigabe"] is True


async def test_ohne_hems_praefix_kein_sensor(hass: HomeAssistant, monkeypatch) -> None:
    await setup_entry(hass, monkeypatch, hems_entity_prefix=None)
    assert hass.states.get(INTERFACE_ENTITY_ID) is None


async def test_unload_entfernt_sensor(hass: HomeAssistant, monkeypatch) -> None:
    entry, _adapter = await setup_entry(hass, monkeypatch)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(INTERFACE_ENTITY_ID) is None
