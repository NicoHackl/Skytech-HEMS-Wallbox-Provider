# API-Referenz

Gemeinsame Felder, Semantik und Status stehen im
[Vertrag](../contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md). Hier nur,
was darüber hinaus für diese Integration gilt.

## Entities

`<prefix>` ist der slugifizierte Anzeigename der Instanz (z. B. `go_e_garage`). Die Entity-IDs
werden beim Anlegen genau so vorgeschlagen; spätere Umbenennungen verwaltet Home Assistant.

| Entity | Plattform | Einheit | Bedingung |
|---|---|---|---|
| `sensor.<prefix>_istleistung` | sensor | W | immer |
| `sensor.<prefix>_spannung_l1` … `_l3` | sensor | V | immer |
| `sensor.<prefix>_ladestrom_l1` … `_l3` | sensor | A | immer |
| `sensor.<prefix>_aktuelle_phasenanzahl` | sensor | – | immer |
| `sensor.<prefix>_wallbox_status` | sensor (enum) | – | immer |
| `sensor.<prefix>_fehler` | sensor (enum) | – | immer |
| `sensor.<prefix>_ladeenergie_sitzung` | sensor | Wh | immer |
| `sensor.<prefix>_ladeenergie_gesamt` | sensor | Wh | immer |
| `sensor.<prefix>_steuerung` | sensor (enum) | – | immer; additive Diagnose |
| `sensor.<prefix>_hems_soll_ladestrom` | sensor | A | mit HEMS-Präfix |
| `sensor.<prefix>_hems_soll_phasenanzahl` | sensor | – | mit HEMS-Präfix und `automatisch` |
| `binary_sensor.<prefix>_fahrzeug_verbunden` | binary_sensor | – | immer |
| `binary_sensor.<prefix>_laedt` | binary_sensor | – | immer |
| `binary_sensor.<prefix>_hems_lebenszeichen` | binary_sensor | – | mit HEMS-Präfix |
| `switch.<prefix>_hems_steuerung_aktiv` | switch | – | mit HEMS-Präfix |
| `number.<prefix>_manueller_ladestrom` | number | A | immer |
| `select.<prefix>_manuelle_phasenanzahl` | select | – | bei `automatisch` |

`sensor.<prefix>_steuerung`: `hems`, `manuell`, `kein_hems_lebenszeichen`,
`ungueltiger_sollwert`, `schreibfehler`. Mess-Entities hängen am Poll, Steuer-Entities nicht.

## Schnittstellen-Entität (D-007)

`sensor.wallbox_provider_schnittstelle` — **eine** Entität für alle Wallboxen mit HEMS-Präfix,
keine Registry-Entität (per `hass.states.async_set`). State: die HEMS-Präfixe, durch Komma
getrennt. Attribute je Wallbox `<prefix>_freigabe` (Bool) und `<prefix>_sperrgrund`
(`nicht_erreichbar`, Fehlerart, `kein_fahrzeug`; mehrere mit Komma; `null` ohne Sperre).
Verbindlich: [Vertrag 2.1](../contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md#provider--hems-sensorwallbox_provider_schnittstelle).

## `WallboxAdapter`-Protocol (`adapters/base.py`)

| Methode | Zweck |
|---|---|
| `connect()` | Transport aufbauen |
| `identify()` | `(seriennummer, firmware)`, prüft die Firmware |
| `read()` | `WallboxState` |
| `set_current(a)` | Ladestrom flüchtig, ≥ `min_current_a` |
| `set_phases(n)` | 1 oder 3 |
| `allow_charging(bool)` | Freigabe ein/aus |
| `close()` | Transport schließen |

Fehler: `WallboxAdapterError`, Firmware: `WallboxFirmwareError`. Nie ein geratener Ersatzwert.

## EVMS-/Watt-Erweiterung — noch nicht implementiert

[Watt-Vertrag mit HEMS](../contract/contract_hems_wallbox_provider/watt_contract.md) und
[EVMS-Vertrag](../contract/contract_evms_wallbox_provider/contract_evms_wallbox_provider.md)
sind die autoritativen Erweiterungsdokumente. Der Provider bleibt aktuell beim
Ampere-Vertrag 2.1. Die HEMS-Vorbereitung allein aktiviert keinen Watt-Betrieb.

Geplant: Wattbudget technisch umsetzen, Quellen HEMS/EVMS/manuell trennen, vollständige
Rückmeldung und RFID-Scans veröffentlichen. RFID dient externer Fahrzeugzuordnung bei
offener go-e-Zugangskontrolle, sofern das konkrete Gerät dieses Verhalten bestätigt.
Noch keine Hardware geliefert; Modell, Firmware, wiederholte Scans und Nebenwirkungen offen.
