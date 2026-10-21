# EVMS: Plan und offene Punkte für den Wallbox-Provider

**Stand: 21.10.2026. Dokumentationsablage im Wallbox-Provider vom Nutzer bestätigt.**

Skytech EVMS erhält ein eigenes Repository. Die vollständige, projektübergreifende
Planung liegt dort; diese Seite ist der Einstieg für die Provider-Arbeit.

- [EVMS-Umsetzungsplan](https://github.com/NicoHackl/Skytech-EVMS/blob/agent/main/docs/umsetzungsplan.md)
- [Offene Fachentscheidungen](https://github.com/NicoHackl/Skytech-EVMS/blob/agent/main/docs/offene-punkte.md)
- [Prüfstand vor Hardwarelieferung](https://github.com/NicoHackl/Skytech-EVMS/blob/agent/main/docs/pruefstand.md)

## Regelwege und Zuständigkeiten

1. HEMS → EVMS → Wallbox-Provider: Fahrzeug-/Anschlusszuordnung im EVMS.
2. HEMS → Wallbox-Provider: direktes physisches Ladeziel.
3. HEMS → eigene HA-Automation: Betreiber implementiert die technische Ansteuerung.

HEMS teilt Wattbudgets zu. Der Provider soll Watt in zulässigen Ladestrom und Phasen
umsetzen. Ein physischer Anschluss hat genau einen Befehlsgeber; keine parallele
Direkt- und EVMS-Steuerung. Der Battery-Provider ist für diese Erweiterung keine Gegenstelle.

## Verträge

| Verbindung | Datei | Stand |
|---|---|---|
| HEMS → Provider, bisher | [Ampere-Vertrag 2.1](../contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md) | Software implementiert, Hardware offen |
| HEMS → Provider, neu | [Watt-Vertrag](../contract/contract_hems_wallbox_provider/watt_contract.md) | HEMS implementiert, Provider noch Entwurf |
| HEMS-Wattprotokoll | [Protokoll 1](../contract/contract_hems_wallbox_provider/charging_protocol.md) | Rückmeldungen und Zuordnungsbestätigung spezifiziert |
| EVMS ↔ Provider | [Vertrag 0.1](../contract/contract_evms_wallbox_provider/contract_evms_wallbox_provider.md) | Beidseitiger Entwurf |

Die Kopien liegen jeweils identisch in den beteiligten Repositories. Data Insight
und HEMS–EVMS sind im [EVMS-Vertragsindex](https://github.com/NicoHackl/Skytech-EVMS/blob/agent/main/contract/README.md) erreichbar.

## Nächste Arbeiten nach Lieferung

1. Modell, Firmware und angeschlossenes Fahrzeug festhalten.
2. RFID im offenen Modus prüfen: bekannte/nicht angelernte Chips, gleicher Chip
   erneut, Scan während Laden, Neustart und Ansteckreihenfolge.
3. Entscheiden, ob Modbus genügt oder die lokale API für Scan-Zeitpunkt/UID nötig ist.
   Keine alte UID als neuen Scan behandeln, führende Nullen und UID-Länge erhalten.
4. Wattumsetzung, Phasenwechsel, dynamische Grenzen und Ausfallverhalten implementieren.
5. Quellenauswahl HEMS/EVMS/manuell und Zuordnungsbindung umsetzen; alte Budgets entwerten.
6. Zusammen mit EVMS und Data Insight die vollständigen Ladeabläufe und Historie prüfen.
7. [Hardware-Abnahme](hardware-abnahme.md) abschließen, dann gemeinsame Migration freigeben.

## Noch offen

Das go-e-Gerät ist noch nicht vorhanden. Sein Verhalten ist nicht bestätigt.
RFID soll nur der externen Zuordnung dienen und keine eigene go-e-Zugangssperre
voraussetzen. Ein EVMS-Modus „unbekanntes Fahrzeug“ ist vorerst ausgeschlossen.
Das Ladezielmodell (dauerhaft je Auto oder anders), Scan-Zuordnungsfenster,
Sitzungsgrenzen, Auswertungsumfang, gemeinsame Anschlusslimits und Wiederanlauf
sind vor finaler Implementierung mit dem Nutzer zu klären.

Der aktuelle Provider bleibt beim bestehenden Ampere-Betrieb. Ein neuer HEMS-Weg
allein ist keine kompatible Providerumstellung und keine Hardwarefreigabe.
