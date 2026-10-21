# Roadmap

| Schritt | Stand |
|---|---|
| Vertrag 1.1, Umsetzungsplan | erledigt 07.10.2026 |
| Lesen und Entities (go-e Modbus) | umgesetzt, an Hardware ungeprüft |
| Steuerung, HEMS-Anbindung, Lebenszeichen, manueller Betrieb | umgesetzt, an Hardware ungeprüft |
| Phasenwechsel „durchreichen" | umgesetzt, `psm`-Werte an Hardware zu bestätigen |
| Hardware-Abnahme | offen — [hardware-abnahme.md](hardware-abnahme.md) |
| RFID-Erkennung als HA-Ereignis | Folgeversion (optional) |
| Weitere Hersteller | als neue Adapter |

## EVMS-/Watt-Erweiterung — noch nicht implementiert

[Watt-Vertrag mit HEMS](../contract/contract_hems_wallbox_provider/watt_contract.md) und
[EVMS-Vertrag](../contract/contract_evms_wallbox_provider/contract_evms_wallbox_provider.md)
sind die autoritativen Erweiterungsdokumente. Der Provider bleibt aktuell beim
Ampere-Vertrag 2.1. Die HEMS-Vorbereitung allein aktiviert keinen Watt-Betrieb.

Geplant: Wattbudget technisch umsetzen, Quellen HEMS/EVMS/manuell trennen, vollständige
Rückmeldung und RFID-Scans veröffentlichen. RFID dient externer Fahrzeugzuordnung bei
offener go-e-Zugangskontrolle, sofern das konkrete Gerät dieses Verhalten bestätigt.
Noch keine Hardware geliefert; Modell, Firmware, wiederholte Scans und Nebenwirkungen offen.
