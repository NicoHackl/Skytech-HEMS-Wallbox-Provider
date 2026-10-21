# Datenmodell

`WallboxState` (`models.py`) ist ein Messwert-Schnappschuss. `None` = nicht verfügbar, `0` = echter
Messwert.

| Feld | Einheit | go-e-Quelle |
|---|---|---|
| `charging_power_w` | W | POWER_TOTAL ÷ 100 |
| `voltage_l1_v` … `l3` | V | VOLT_L1..L3 |
| `current_l1_a` … `l3` | A | AMP_L1..L3 ÷ 10 |
| `active_phase_count` | – | PHASES, Bits 0–2 (hinter dem Schütz) |
| `vehicle_state` | enum | CAR_STATE |
| `vehicle_connected` | bool | CAR_STATE ∈ {2, 3, 4} |
| `is_charging` | bool | CAR_STATE = 2 |
| `fault` | enum | ERROR |
| `session_energy_wh` | Wh | ENERGY_CHARGE × 10 ÷ 3600 |
| `total_energy_wh` | Wh | ENERGY_TOTAL × 100 |
| `max_current_a` | A | AMPERE_MAX (≥ 6, sonst `None`) |

Registeradressen: Kopf von `adapters/goe_modbus.py`.

## Normalisierte Werte

| `vehicle_state` | CAR_STATE |
|---|---|
| `unbekannt` | 0 und unbekannte Werte |
| `bereit` | 1 |
| `laedt` | 2 |
| `wartet_auf_fahrzeug` | 3 |
| `ladung_beendet` | 4 |
| `fehler` | 5 |

| `fault` | ERROR |
|---|---|
| `kein_fehler` | 0 |
| `fehlerstrom` | 1, 2, 11 |
| `phasenfehler` | 3 |
| `ueberspannung` | 4 |
| `ueberstrom` | 5 |
| `erdung` | 8 |
| `schuetz` | 9, 10 |
| `uebertemperatur` | 13 |
| `kabelverriegelung` | 15, 16 |
| `sonstiger_fehler` | alle übrigen |

Persistenz: keine. Betriebsart, manuelle Werte und Lebenszeichen leben im Arbeitsspeicher; nach
einem Neustart gilt HEMS-Betrieb, manueller Strom 0, manuelle Phasen 1.

## EVMS-/Watt-Erweiterung — noch nicht implementiert

[Watt-Vertrag mit HEMS](../contract/contract_hems_wallbox_provider/watt_contract.md) und
[EVMS-Vertrag](../contract/contract_evms_wallbox_provider/contract_evms_wallbox_provider.md)
sind die autoritativen Erweiterungsdokumente. Der Provider bleibt aktuell beim
Ampere-Vertrag 2.1. Die HEMS-Vorbereitung allein aktiviert keinen Watt-Betrieb.

Geplant: Wattbudget technisch umsetzen, Quellen HEMS/EVMS/manuell trennen, vollständige
Rückmeldung und RFID-Scans veröffentlichen. RFID dient externer Fahrzeugzuordnung bei
offener go-e-Zugangskontrolle, sofern das konkrete Gerät dieses Verhalten bestätigt.
Noch keine Hardware geliefert; Modell, Firmware, wiederholte Scans und Nebenwirkungen offen.
