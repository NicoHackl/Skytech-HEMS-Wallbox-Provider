# Architektur

```text
SkytechHEMS ── input_number.ems_<prefix>_* ──► HA ──► hems_bridge.py ──► Adapter ──► Wallbox
SkytechHEMS ── sensor.hems_schnittstelle ───► HA ──► heartbeat.py
SkytechHEMS ◄── sensor.<provider>_* ── HA ◄── Coordinator ◄── Adapter ◄── Wallbox
SkytechHEMS ◄── sensor.wallbox_provider_schnittstelle ── HA ◄── interface.py
```

| Datei | Verantwortung | Darf nicht |
|---|---|---|
| `__init__.py` | Entry einrichten: Adapter wählen, Coordinator, Steuerung, Platforms | Herstellerdetails kennen (außer in `build_adapter`) |
| `coordinator.py` | Pollen, Takt bei Ausfall auf 30 s strecken, nach Wiederverbindung Sollwert anstoßen | Schreiben |
| `hems_bridge.py` | Wirksamen Sollwert bilden (Betriebsart, Lebenszeichen, Validierung) und als Befehlsfolge schreiben; Neuschreiben; Stoppvorrang | Register kennen; HEMS-Helfer schreiben |
| `heartbeat.py` | Regeln des Lebenszeichens, ohne HA-Import | Auf HA zugreifen |
| `interface.py` | `sensor.wallbox_provider_schnittstelle` für alle Wallboxen mit HEMS-Präfix (D-007): Freigabe und Sperrgrund je Wallbox, per `hass.states.async_set` | Sollwerte schreiben |
| `adapters/base.py` | `WallboxAdapter`-Protocol, `WallboxAdapterError`, `WallboxFirmwareError` | — |
| `adapters/goe_modbus.py` | go-e-Register, Umrechnung, Firmware-Prüfung | Steuerlogik |
| `adapters/modbus_tcp.py` | Modbus TCP (Funktionen 3, 4, 16), eine Sperre je Einzelzugriff | Fachlogik |
| `entity.py` | Geräteinfo, Unique IDs, vertragsgemäße Entity-IDs | — |
| `sensor.py`, `binary_sensor.py` | Mess- und Diagnose-Entities | Schreiben |
| `switch.py`, `number.py`, `select.py` | Betriebsart, manueller Strom, manuelle Phasen | Direkt an den Adapter schreiben |
| `config_flow.py` | Einrichtung mit Verbindungstest, Optionen | Geheimnisse loggen |

## Invarianten

1. **Nur der Adapter kennt das Gerät.** Coordinator, Steuerung und Platforms kennen nur das
   `WallboxAdapter`-Protocol.
2. **Der Provider schreibt nie HEMS-Helfer** (`input_*`), nur Gerätebefehle über den Adapter.
3. **Ein fehlender Messwert ist nicht 0.** `None` → Entity nicht verfügbar.
4. **Ein Stopp überholt jede positive Folge.** Vor jedem positiven Einzelschritt wird der
   wirksame Sollwert neu gebildet (D-003).
5. **Ohne frisches Lebenszeichen kein positiver HEMS-Sollwert** (D-004).
6. **Nur das flüchtige Stromregister** wird geschrieben, nie das EEPROM-Register.

## Ablauf eines Befehls

1. Auslöser: Helferänderung, Lebenszeichen-Wechsel, Neuschreib-Takt (`keepalive_s`),
   Bedienung, Wiederverbindung.
2. `effective_target()`: manuell → manuelle Werte; HEMS → bei frischem Lebenszeichen
   validierter Schnappschuss, sonst Stopp.
3. Stopp: Freigabe aus. Positiv: Phasenmodus (nur bei Änderung, nur `automatisch`) → Strom →
   Freigabe ein.
4. Läuft schon eine Folge, wird sie danach mit dem neuesten Wert wiederholt (nie parallel).

## EVMS-/Watt-Erweiterung — noch nicht implementiert

[Watt-Vertrag mit HEMS](../contract/contract_hems_wallbox_provider/watt_contract.md) und
[EVMS-Vertrag](../contract/contract_evms_wallbox_provider/contract_evms_wallbox_provider.md)
sind die autoritativen Erweiterungsdokumente. Der Provider bleibt aktuell beim
Ampere-Vertrag 2.1. Die HEMS-Vorbereitung allein aktiviert keinen Watt-Betrieb.

Geplant: Wattbudget technisch umsetzen, Quellen HEMS/EVMS/manuell trennen, vollständige
Rückmeldung und RFID-Scans veröffentlichen. RFID dient externer Fahrzeugzuordnung bei
offener go-e-Zugangskontrolle, sofern das konkrete Gerät dieses Verhalten bestätigt.
Noch keine Hardware geliefert; Modell, Firmware, wiederholte Scans und Nebenwirkungen offen.
