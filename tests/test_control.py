"""Tests der Steuerung (hems_bridge.py) gegen den Vertrag HEMS ↔ Wallbox-Provider."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

import custom_components.wallbox_provider.heartbeat as heartbeat_module
from custom_components.wallbox_provider.const import (
    CONF_KEEPALIVE,
    PHASE_MODE_FIXED_3,
)
from tests.conftest import (
    CURRENT_ENTITY,
    PHASE_ENTITY,
    STATUS_ENTITY,
    entity_ids_by_key,
    hems_zyklus,
    set_hems,
    setup_entry,
)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    now = [1000.0]

    class _FakeTime:
        @staticmethod
        def monotonic() -> float:
            return now[0]

    monkeypatch.setattr(heartbeat_module, "time", _FakeTime)
    return now


async def _tick(hass: HomeAssistant, seconds: float) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


def _control(entry):
    return entry.runtime_data.control


# ---- Start und Lebenszeichen ----


async def test_start_ohne_lebenszeichen_stoppt(hass: HomeAssistant, monkeypatch) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    assert adapter.calls == [("allow", False)]
    assert _control(entry).status == "kein_hems_lebenszeichen"


async def test_alter_positiver_sollwert_beim_start_startet_nicht(
    hass: HomeAssistant, monkeypatch
) -> None:
    hass.states.async_set(PHASE_ENTITY, "3")
    hass.states.async_set(CURRENT_ENTITY, "10")
    hass.states.async_set(STATUS_ENTITY, "57", {"zyklus_intervall_s": 30})
    entry, adapter = await setup_entry(hass, monkeypatch)
    assert adapter.calls == [("allow", False)]

    adapter.calls.clear()
    await hems_zyklus(hass)
    assert adapter.calls == [("phases", 3), ("current", 10), ("allow", True)]
    assert _control(entry).status == "hems"


async def test_hems_sollwert_wird_durchgereicht(hass: HomeAssistant, monkeypatch) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    adapter.calls.clear()

    await set_hems(hass, "10", "3")
    assert adapter.calls[-3:] == [("phases", 3), ("current", 10), ("allow", True)]
    assert _control(entry).last_hems_current_a == 10
    assert _control(entry).last_hems_phases == 3


async def test_phasenmodus_nur_bei_aenderung(hass: HomeAssistant, monkeypatch) -> None:
    _entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    await set_hems(hass, "10", "3")
    adapter.calls.clear()

    hass.states.async_set(CURRENT_ENTITY, "12")
    await hass.async_block_till_done()
    assert adapter.calls == [("current", 12), ("allow", True)]


async def test_null_ampere_nimmt_freigabe_zurueck(hass: HomeAssistant, monkeypatch) -> None:
    _entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    await set_hems(hass, "10", "3")
    adapter.calls.clear()

    hass.states.async_set(CURRENT_ENTITY, "0")
    await hass.async_block_till_done()
    assert adapter.calls == [("allow", False)]


@pytest.mark.parametrize(
    ("current", "phases"),
    [("3", "1"), ("-6", "1"), ("10.5", "1"), ("17", "1"), ("unavailable", "1"),
     ("abc", "1"), ("10", "2"), ("10", "unknown")],
)
async def test_ungueltiger_sollwert_stoppt(
    hass: HomeAssistant, monkeypatch, current: str, phases: str
) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    await set_hems(hass, "10", "1")
    adapter.calls.clear()

    await set_hems(hass, current, phases)
    assert adapter.calls[-1] == ("allow", False)
    assert ("current", 10) not in adapter.calls
    assert all(value not in (3, 17) for kind, value in adapter.calls if kind == "current")
    assert _control(entry).status == "ungueltiger_sollwert"


async def test_ausbleibendes_lebenszeichen_stoppt_und_kommt_zurueck(
    hass: HomeAssistant, monkeypatch, clock
) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    await set_hems(hass, "10", "3")
    adapter.calls.clear()

    clock[0] += 91  # Frist 3 × 30 s
    await _tick(hass, 5)
    assert adapter.calls == [("allow", False)]
    assert _control(entry).status == "kein_hems_lebenszeichen"
    assert _control(entry).last_hems_current_a == 0

    adapter.calls.clear()
    await hems_zyklus(hass)
    assert adapter.calls == [("current", 10), ("allow", True)]


# ---- Neuschreiben, Fehler, Wiederholung ----


async def test_sollwert_wird_regelmaessig_neu_geschrieben(
    hass: HomeAssistant, monkeypatch
) -> None:
    _entry, adapter = await setup_entry(hass, monkeypatch, options={CONF_KEEPALIVE: 30})
    await hems_zyklus(hass)
    await set_hems(hass, "10", "3")
    adapter.calls.clear()

    await _tick(hass, 31)
    assert adapter.calls == [("current", 10), ("allow", True)]


async def test_schreibfehler_bleibt_sichtbar_und_wird_wiederholt(
    hass: HomeAssistant, monkeypatch
) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    adapter.fail_writes = True
    await set_hems(hass, "10", "3")
    control = _control(entry)
    assert control.status == "schreibfehler"
    assert control.last_hems_current_a is None
    ids = entity_ids_by_key(hass, entry)
    assert hass.states.get(ids["hems_soll_ladestrom"]).state == "unavailable"

    adapter.fail_writes = False
    adapter.calls.clear()
    await _tick(hass, 31)
    # Phasenmodus war nie erfolgreich geschrieben → wird mit wiederholt.
    assert adapter.calls == [("phases", 3), ("current", 10), ("allow", True)]
    assert control.status == "hems"
    assert hass.states.get(ids["hems_soll_ladestrom"]).state == "10"


async def test_stopp_ueberholt_laufende_positive_folge(hass: HomeAssistant, monkeypatch) -> None:
    """Kommt während des Phasenschritts ein Stopp, entfallen Strom und Freigabe ein."""
    _entry, adapter = await setup_entry(hass, monkeypatch)
    await hems_zyklus(hass)
    await set_hems(hass, "10", "1")
    adapter.calls.clear()

    async def stopp_waehrend_phasenwechsel(kind, value):
        if kind == "phases":
            hass.states.async_set(CURRENT_ENTITY, "0")

    adapter.on_write = stopp_waehrend_phasenwechsel
    hass.states.async_set(PHASE_ENTITY, "3")
    await hass.async_block_till_done()

    assert adapter.calls[0] == ("phases", 3)
    assert ("current", 10) not in adapter.calls
    assert ("allow", True) not in adapter.calls
    assert adapter.calls[-1] == ("allow", False)


# ---- Phasenbetrieb ----


async def test_feste_phasenzahl_schreibt_nie_den_phasenmodus(
    hass: HomeAssistant, monkeypatch
) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch, phase_mode=PHASE_MODE_FIXED_3)
    await hems_zyklus(hass)
    hass.states.async_set(CURRENT_ENTITY, "10")  # kein Phasenhelfer nötig
    await hass.async_block_till_done()
    assert ("phases", 3) not in adapter.calls
    assert adapter.calls[-2:] == [("current", 10), ("allow", True)]
    ids = entity_ids_by_key(hass, entry)
    assert "hems_soll_phasenanzahl" not in ids
    assert "manuelle_phasenanzahl" not in ids


# ---- Betriebsart manuell ----


async def test_manuell_ignoriert_hems_und_nutzt_manuelle_werte(
    hass: HomeAssistant, monkeypatch
) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch)
    ids = entity_ids_by_key(hass, entry)
    await hems_zyklus(hass)
    await set_hems(hass, "10", "3")
    adapter.calls.clear()

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": ids["hems_steuerung_aktiv"]}, blocking=True
    )
    assert adapter.calls == [("allow", False)]  # manueller Standard 0 A
    assert _control(entry).status == "manuell"

    adapter.calls.clear()
    await hass.services.async_call(
        "select", "select_option",
        {"entity_id": ids["manuelle_phasenanzahl"], "option": "1"}, blocking=True,
    )
    await hass.services.async_call(
        "number", "set_value", {"entity_id": ids["manueller_ladestrom"], "value": 8},
        blocking=True,
    )
    assert adapter.calls[-3:] == [("phases", 1), ("current", 8), ("allow", True)]

    adapter.calls.clear()
    hass.states.async_set(CURRENT_ENTITY, "16")
    await hass.async_block_till_done()
    assert adapter.calls == []  # HEMS-Helfer wirkt im manuellen Betrieb nicht

    adapter.calls.clear()
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": ids["hems_steuerung_aktiv"]}, blocking=True
    )
    assert adapter.calls == [("phases", 3), ("current", 16), ("allow", True)]


async def test_manueller_strom_unter_minimum_wird_abgelehnt(
    hass: HomeAssistant, monkeypatch
) -> None:
    from homeassistant.exceptions import ServiceValidationError

    entry, _adapter = await setup_entry(hass, monkeypatch)
    ids = entity_ids_by_key(hass, entry)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "number", "set_value", {"entity_id": ids["manueller_ladestrom"], "value": 3},
            blocking=True,
        )


async def test_ohne_hems_praefix_dauerhaft_manuell(hass: HomeAssistant, monkeypatch) -> None:
    entry, adapter = await setup_entry(hass, monkeypatch, hems_entity_prefix=None)
    ids = entity_ids_by_key(hass, entry)
    assert "hems_steuerung_aktiv" not in ids
    assert "hems_lebenszeichen" not in ids
    assert "hems_soll_ladestrom" not in ids
    assert "manueller_ladestrom" in ids
    assert adapter.calls == [("allow", False)]
    assert _control(entry).status == "manuell"
