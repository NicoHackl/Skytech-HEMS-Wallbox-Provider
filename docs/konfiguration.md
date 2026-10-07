# Konfiguration

Keine Umgebungsvariablen und keine Geheimnisse: die go-e-Modbus-Schnittstelle hat keine
Anmeldung. Alle Werte speichert Home Assistant im Config-Entry.

## Einrichtung (`entry.data`)

| Feld | Default | Bedeutung |
|---|---|---|
| `display_name` | `go-e <Seriennummer>` | Gerätename, daraus `<provider_prefix>` |
| `host` | – | IP-Adresse der Wallbox |
| `port` | 502 | Modbus-Port |
| `unit_id` | 1 | Modbus-Geräteadresse |
| `hems_entity_prefix` | leer | HEMS-`entity_prefix`; leer = dauerhaft manuell |
| `phase_mode` | `automatisch` | `automatisch`, `fest_1`, `fest_3` |

Unique ID: Seriennummer der Wallbox.

## Optionen (`entry.options`, Änderung lädt neu)

| Feld | Default | Bereich | Bedeutung |
|---|---|---|---|
| `update_interval_seconds` | 5 | 1–60 | Abfrageintervall; bei Ausfall 30 s |
| `keepalive_seconds` | 30 | 5–300 | Sollwert erneut senden |
| `hems_timeout_factor` | 3 | 2–10 | Frist ohne Lebenszeichen × HEMS-Zykluszeit; nur mit HEMS-Präfix |

## SkytechHEMS-Seite

Beispiel der HEMS-Gerätekonfiguration: [Vertrag](../contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md#hems-konfiguration).
`phase_mode` muss zu HEMS `phases` passen: `automatisch` ↔ `"1,3"`, `fest_1` ↔ `"1"`,
`fest_3` ↔ `"3"`.
