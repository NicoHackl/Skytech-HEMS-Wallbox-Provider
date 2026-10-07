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
