"""Entity-IDs, Verfügbarkeit und Einheiten gemäß Vertrag."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from tests.conftest import hems_zyklus, make_state, setup_entry

CONTRACT_IDS = [
    "sensor.go_e_garage_istleistung",
    "sensor.go_e_garage_spannung_l1",
    "sensor.go_e_garage_spannung_l2",
    "sensor.go_e_garage_spannung_l3",
    "sensor.go_e_garage_aktuelle_phasenanzahl",
    "sensor.go_e_garage_hems_soll_ladestrom",
    "sensor.go_e_garage_hems_soll_phasenanzahl",
    "binary_sensor.go_e_garage_fahrzeug_verbunden",
    "binary_sensor.go_e_garage_laedt",
    "sensor.go_e_garage_wallbox_status",
    "sensor.go_e_garage_fehler",
    "sensor.go_e_garage_ladestrom_l1",
    "sensor.go_e_garage_ladestrom_l2",
    "sensor.go_e_garage_ladestrom_l3",
    "sensor.go_e_garage_ladeenergie_sitzung",
    "sensor.go_e_garage_ladeenergie_gesamt",
    "switch.go_e_garage_hems_steuerung_aktiv",
    "binary_sensor.go_e_garage_hems_lebenszeichen",
    "number.go_e_garage_manueller_ladestrom",
    "select.go_e_garage_manuelle_phasenanzahl",
]


async def test_entity_ids_entsprechen_dem_vertrag(hass: HomeAssistant, monkeypatch) -> None:
    await setup_entry(hass, monkeypatch)
    for entity_id in CONTRACT_IDS:
        assert hass.states.get(entity_id) is not None, entity_id


async def test_messwerte_und_einheiten(hass: HomeAssistant, monkeypatch) -> None:
    _entry, adapter = await setup_entry(hass, monkeypatch)
    state = hass.states.get("sensor.go_e_garage_istleistung")
    assert state.state == "0.0"  # 0 ist ein echter Messwert
    assert state.attributes["unit_of_measurement"] == "W"
    assert hass.states.get("sensor.go_e_garage_spannung_l2").state == "231.0"
    assert hass.states.get("binary_sensor.go_e_garage_fahrzeug_verbunden").state == "on"
    assert hass.states.get("sensor.go_e_garage_fehler").state == "kein_fehler"
    assert hass.states.get("switch.go_e_garage_hems_steuerung_aktiv").state == "on"


async def test_fehlender_messwert_ist_nicht_null(hass: HomeAssistant, monkeypatch) -> None:
    _entry, adapter = await setup_entry(hass, monkeypatch)
    adapter.state = make_state(charging_power_w=None)
    await _entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.go_e_garage_istleistung").state == "unavailable"
    assert hass.states.get("sensor.go_e_garage_spannung_l1").state == "230.0"


async def test_pollfehler_macht_messwerte_unverfuegbar(hass: HomeAssistant, monkeypatch) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    adapter.fail_reads = True
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.go_e_garage_istleistung").state == "unavailable"
    assert hass.states.get("binary_sensor.go_e_garage_laedt").state == "unavailable"
    # Steuerungsbezogene Entities hängen nicht am Poll.
    assert hass.states.get("binary_sensor.go_e_garage_hems_lebenszeichen").state == "on"


async def test_wiederverbindung_uebernimmt_sollwert_sofort(
    hass: HomeAssistant, monkeypatch
) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    adapter.fail_reads = True
    await entry.runtime_data.async_refresh()
    adapter.fail_reads = False
    adapter.calls.clear()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    assert ("allow", False) in adapter.calls
