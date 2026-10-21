# Vertrag: Skytech EVMS ↔ Skytech HEMS Wallbox Provider

**Version: 0.1 — 21.10.2026. Status: Entwurf auf beiden Seiten, Hardware offen.**

## Verantwortung

EVMS verwaltet Fahrzeugidentität, Zuordnung und fahrzeugbezogene Einschränkungen.
Der Provider liest Gerätewerte, RFID-Scans und Fähigkeiten und setzt Wattbudgets
technisch in Strom, Phasen und Ladefreigabe um. Stationäre Speicher sind nicht beteiligt.

## Vorgesehene Richtung und Inhalt

Provider → EVMS über `sensor.wallbox_provider_schnittstelle`: stabile physische
Anschlusskennung, Verbindung/Zustand, Istleistung, Gesamt-/Sitzungsenergie mit Einheit,
aktuelle Grenzen und Phasenfähigkeiten, Freigabe/Sperrgrund, Messfrische sowie RFID-Scan.
EVMS → Provider über `sensor.evms_schnittstelle`: je physischem Anschluss zugeordnete
Fahrzeug-/Sitzungskennung, Budget in Watt, zulässige Fahrzeuggrenzen und Gültigkeit.

Das konkrete Feldschema dieser beiden Richtungen ist **noch nicht implementiert**.
Es wird nach Hardwareprüfung ergänzt. Nicht die bereits implementierte HEMS-Rückmeldung
mit einem fertigen EVMS–Provider-Protokoll verwechseln.

## Verbindliche Semantik des Zielbilds

- Ein Anschluss hat genau einen konfigurierten Befehlsgeber: HEMS, EVMS oder manuell.
- In EVMS-Betrieb akzeptiert der Provider keine direkte HEMS-Vorgabe für denselben Anschluss.
- Vorgaben sind an eine aktuelle Anschluss-/Fahrzeugzuordnung gebunden. Ein Wechsel
  entwertet alle älteren positiven Vorgaben; zunächst Stopp.
- Provider prüft EVMS-Frische UND die erhaltene HEMS-Gültigkeit. EVMS darf ein abgelaufenes
  HEMS-Budget nicht durch neue Veröffentlichungen verlängern.
- Null und ungültige/abgelaufene Vorgaben stoppen. Geräteausfall kann die Zustellung
  verhindern; ein geräteseitiger Watchdog ist an Hardware zu klären.
- Strom-/Phasenwahl bleibt innerhalb des Wattbudgets und aller wirksamen Grenzen.
  Phasenwechselverfahren, Toleranz und Timings sind Hardware-Abnahmepunkte.
- Kein Betrieb mit unbekanntem Fahrzeug. Keine geratenen Zuordnungen nach Neustart.

## RFID zur externen Verarbeitung

RFID soll ausschließlich die externe Fahrzeugzuordnung unterstützen; die go-e soll
mit offener Zugangskontrolle weiter durch den Provider steuerbar bleiben.
Das ist eine zu prüfende Anforderung, keine bestätigte Geräteeigenschaft.

Ein Scan besteht fachlich aus Anschluss, Kartenkennung und eindeutiger neuer Scan-Kennung
beziehungsweise Geräte-Lesezeit plus Bootkennung. Dieselbe Karte zweimal vorhalten
muss zwei Scans ergeben. Der letzte gespeicherte Kartenwert ist kein neuer Scan.
Beim Start keinen restaurierten Kartenwert als Ereignis ausgeben. Empfangszeit und
Geräte-Lesezeit unterscheiden; ein erst später abgefragter Wert beweist keine neue Lesung.
Verpasste Scans durch Polling sind als Grenze zu prüfen.

Modbus `RFID_CARD` dokumentiert die letzte UID, aber keinen Ereigniszähler.
Die lokale API listet `lri`, `lrr` und `rde`; Firmwareunterstützung, Zugriffsbedingungen
und Nebenwirkungen sind offen. Kartenfreigabe (`UNLOCKED_BY`) ist etwas anderes als UID.
Normierung muss UID-Länge und führende Nullen erhalten; niemals einfach Nullen abschneiden.

Quellen, geprüft am 21.10.2026:
- [go-e Modbus](https://github.com/goecharger/go-eCharger-API-v2/blob/main/modbus-en.md)
- [go-e API-Felder](https://github.com/goecharger/go-eCharger-API-v2/blob/main/API_KEYS_FIRMWARE/apikeys-en.md)
- [go-e Zugangskontrolle](https://go-e.com/de-de/support/faqs)

Offen: Modell/Firmware, Scans im offenen Modus, bekannte/nicht angelernte Karten,
Laden während Scan, gleicher Chip erneut, Reset bei Neustart, Transport und Scanfenster.
