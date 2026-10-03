# Technische Prüfung und offene Fragen — Wallbox Provider V1

**Dokumentstand:** 03.10.2026  
**Grundlage:** Prüfung vom 02.10.2026  
**Status:** Entscheidungsgrundlage; offene Fragen sind noch nicht beantwortet.

## 1. Zweck und Gesamtbewertung

Dieses Dokument bündelt die offenen Fragen an den Projektverantwortlichen, nachgewiesene
Fehler, Widersprüche und technische Hürden sowie Empfehlungen zur Überarbeitung des Plans.
Es ändert weder den bestehenden Vertrag noch den Umsetzungsumfang. Empfehlungen sind keine
bereits getroffenen Entscheidungen.

Die Grundarchitektur ist sinnvoll: SkytechHEMS entscheidet über die Energieverteilung; der
Provider übersetzt Sollwerte in Gerätebefehle und veröffentlicht Messwerte. Der aktuelle
Entwurf ist jedoch noch nicht bereit für eine unveränderte Umsetzung. Insbesondere die
Phasenumschaltung und der Umgang mit Abschaltung, Ausfällen und Wiederanlauf müssen vorab
präzisiert werden. Für die automatische Phasenumschaltung ist zudem ein Fehler im bestehenden
HEMS zu beheben.

Geprüfte Grundlagen:

- [Umsetzungsplan V1](plan_v1.md)
- [Vertrag im Wallbox-Provider](contract/contract_hems_wallbox_provider.md)
- [Vertrag im HEMS](../SkytechHEMS/contract/contract_hems_wallbox_provider.md)
- HEMS-Code für regelbare Geräte, Regelzyklen, HA-Schreibzugriffe und Notabschaltung
- HEMS-Dokumentation einschließlich bekannter Lücken
- Battery-Provider-Bridge als vorhandene Architekturvorlage
- Öffentliche Herstellerdokumentation von go-e und Entwicklerdokumentation von Home Assistant

Die beiden Vertragskopien waren bei der Prüfung wortgleich. Im Wallbox-Provider liegen bisher
Plan und Vertrag vor; eine Provider-Implementierung konnte deshalb noch nicht geprüft werden.

## 2. Offene Fragen an den Projektverantwortlichen

### 2.1 Hardware und Installation

**F-01 — Welche Hardware wird konkret eingesetzt?**

- Gemini oder Gemini 2.0, gegebenenfalls flex, und genaue Leistungsvariante?
- Welche Firmware ist installiert?
- Welches Fahrzeug beziehungsweise welche Fahrzeuge sollen laden?
- Ist der Anschluss dreiphasig, und gibt es eine abweichende installierte Strombegrenzung?
- Stehen Wallbox und Fahrzeug für wiederholte Hardwaretests zur Verfügung?

**Antwort:** Offen.

**F-02 — Wie wird der Zugang zur Wallbox freigegeben?**

Wird RFID verwendet, oder ist die Wallbox grundsätzlich frei zugänglich? Soll eine vorhandene
RFID-Autorisierung über PV-Ladepausen und Phasenwechsel hinweg erhalten bleiben?

**Antwort:** Offen. Der Entwurf verlangt bereits, die Zugangskontrolle nicht zu umgehen.

**F-03 — Welche bestehenden Steuerungen sind aktiv?**

Gibt es go-e-App-Zeitpläne, PV-Steuerung, einen go-e Controller, OCPP, andere Integrationen oder
HA-Automationen, die Ladestrom, Phasenmodus oder Ladefreigabe verändern? Welche davon sollen
weiter genutzt werden?

**Antwort:** Offen. Konkurrierende Regelung muss für den vorgesehenen Betrieb ausgeschlossen werden.

### 2.2 Auslieferung und Umfang

**F-04 — Ist mit „Add-on“ eine Custom-Integration oder ein Supervisor-Dienst gemeint?**

Der Plan beschreibt eine Home-Assistant-Custom-Integration mit Config Flow und HACS-Auslieferung.
Ist das die gewünschte Form, oder wird ein eigenständiges Supervisor-Add-on erwartet?

**Empfehlung:** Custom-Integration wie im Plan; sie passt zur direkten Beobachtung von HA-Helfern.

**Antwort:** Offen.

**F-05 — Wie verbindlich ist der Ausschluss von HEMS-Änderungen?**

Darf der reproduzierte Phasenfehler im HEMS im Rahmen dieses Vorhabens behoben werden? Sind
kleine Vertragserweiterungen für zusammengehörige Befehle, Lebenszeichen oder Rückmeldungen
möglich? Alternativ: Soll eine erste Freigabe zunächst auf eine feste Phasenzahl begrenzt werden?

**Empfehlung:** Den Fehler vor Freigabe automatischer Phasenwechsel beheben. Den Ausschluss von
HEMS-Änderungen im Plan entsprechend anpassen.

**Antwort:** Offen.

**F-06 — Soll der Provider ohne HEMS nur messen oder auch manuell steuern können?**

Der Vertrag beschreibt bei leerem HEMS-Präfix einen Entity-Lieferanten, erwähnt an anderer Stelle
aber manuelle Befehle. Soll es eigene Bedienelemente für Strom, Phasen und Ladefreigabe geben?
Wie soll bei manueller Bedienung und anschließendem Fortsetzen die Kontrolle übergeben werden?

**Antwort:** Offen. Eine öffentliche manuelle Steuerschnittstelle ist bisher nicht definiert.

### 2.3 Abschaltung, Ausfälle und Wiederanlauf

**F-07 — Was soll bei Ausfall des HEMS passieren, wenn HA weiterläuft?**

Soll mit dem letzten Sollwert weitergeladen oder nach einer definierten Frist gestoppt werden?
Falls gestoppt werden soll: Welche Frist ist akzeptabel?

**Empfehlung:** Falls ein zeitbegrenztes Weiterladen gewünscht ist, ein separates HEMS-Lebenszeichen
vorsehen. Das Alter einer Sollwertänderung kann einen HEMS-Ausfall nicht zuverlässig erkennen.

**Antwort:** Offen.

**F-08 — Soll die HEMS-Notabschaltung auch bei pausierter Bridge greifen?**

Der Schalter pausiert laut Entwurf sämtliche automatische Übersetzung. Soll eine Notabschaltung
diese Pause übersteuern, auch wenn die Wallbox gerade manuell betrieben wird?

**Empfehlung:** Eine übergeordnete Notabschaltung ausdrücklich definieren. Dafür muss der Provider
Notabschaltung und normale HEMS-Vorgabe unterscheiden können; der Stromwert allein liefert diese
Unterscheidung nicht.

**Antwort:** Offen.

**F-09 — Welche Reaktionszeit und Fehlerquittierung werden erwartet?**

Wie schnell muss ein Stopp bei erreichbarer Wallbox umgesetzt werden? Soll nach einem
fehlgeschlagenen Phasenwechsel automatisch erneut gestartet werden, oder erst nach Quittierung?
Wie soll sich die Wallbox nach einer vorübergehenden Kommunikationsstörung verhalten?

**Empfehlung:** Stopp gegenüber positiven Befehlen priorisieren; Kommunikationsfehler und
fehlgeschlagene Phasenwechsel getrennt behandeln. Konkrete Fristen anhand der Hardware festlegen.

**Antwort:** Offen.

**F-10 — Ist die automatische Reaktivierung nach einem Neustart gewünscht?**

Der Vertrag setzt die HEMS-Steuerung nach einem Neustart auf aktiv. Soll auch eine zuvor bewusst
pausierte Bridge automatisch wieder aktiv werden? Darf ein wiederhergestellter positiver
HEMS-Helferwert unmittelbar einen Ladestart auslösen, oder muss zunächst ein frischer HEMS-Zyklus
nachgewiesen sein?

**Antwort:** Offen; der bisherige Neustart-Default ist beschrieben, seine Konsequenzen sollten
ausdrücklich bestätigt werden.

### 2.4 Phasenbetrieb und Betriebsgrenzen

**F-11 — Welche Phasenbetriebsarten müssen V1 unterstützen?**

Nur automatische Umschaltung zwischen einer und drei Phasen oder zusätzlich feste Ein- und
Dreiphasenkonfigurationen? Wie soll die feste Einstellung im Provider konfiguriert werden?

**Empfehlung:** Feste Phasenzahl und automatische Umschaltung explizit unterscheiden; nicht aus
einem fehlenden Helfer auf die gewünschte Phasenzahl schließen.

**Antwort:** Offen.

**F-12 — Welche Priorität haben Ladeunterbrechungen und Fehlerabschaltung?**

Ist das Vermeiden zusätzlicher Stop-/Start-Zyklen ein Ziel für erfolgreiche normale Wechsel,
während bei Fehlern ausdrücklich gestoppt werden darf? Sind für das konkrete Fahrzeug
Einschränkungen bei Ladepausen oder Phasenwechseln bekannt?

**Empfehlung:** Das Komfortziel auf den erfolgreichen Normalablauf begrenzen. Ein Fehlerstopp
darf dadurch nicht verhindert werden.

**Antwort:** Offen.

## 3. Nachgewiesene Fehler und technische Hürden

### T-01 — Kritisch: HEMS schreibt beim Phasenwechsel nicht immer den passenden Strom

**Einordnung:** Im vorhandenen HEMS-Code reproduzierter Fehler.

Mit den Regelparametern des Vertragsbeispiels wurde ein vollständiger
`EMSController.run_cycle()` ausgeführt:

| Größe | Wert |
|---|---|
| Bisheriger Phasensollwert | 1 |
| Bisheriger Stromsollwert | 16 A |
| Tatsächliche Wallboxleistung | 3.680 W |
| Zusätzlicher Netzüberschuss | 1.320 W |
| Verfügbarer Pool | 5.000 W |
| Technische Grenzen | 6–16 A |
| Hoch-/Runterregelzeit | jeweils 60 s |
| Maximale Änderung | 2 A |
| Totband | 1 A |

Der Zyklus erzeugte ausschließlich:

```text
input_number.ems_wallbox_anzahl_phase = 3
```

Der Stromhelfer blieb auf 16 A. Nach dem geplanten Provider-Ablauf könnten nach bestätigtem
Wechsel damit drei Phasen mit jeweils 16 A freigegeben werden: bei 230 V insgesamt 11.040 W.
Das ist eine mögliche Freigabe gemäß Vertrag, keine an Hardware gemessene Leistungsaufnahme.

Die Ursache liegt im Zusammenspiel von Phasenwahl, Rampenbegrenzung und Totband:
Im reproduzierten Fall werden intern zunächst 4.140 W gebildet. Gegenüber dem alten Sollwert
von 3.680 W beträgt die Änderung 460 W und unterschreitet das neue dreiphasige Totband von
690 W. Der Stromschreibbefehl entfällt, während der Phasenbefehl erhalten bleibt.

**Folge:** Debounce kann diesen Fehler nicht beheben, weil kein zweiter Befehl folgt.

**Empfehlung:** Phasen- und Stromausgabe im HEMS gemeinsam prüfen und korrigieren; Regressionstest
über einen vollständigen Regelzyklus ergänzen. Die neue Konstellation muss auch bei Totband,
Rampenwartezeit und Schreibfehlern eine sinnvolle Leistungsanforderung darstellen.

Codebezug: [devices.py](../SkytechHEMS/app/ems/devices.py), insbesondere `select_phases()`,
`calculate_ramp()` und `get_write_ops()`.

### T-02 — Kritisch: Registertabelle enthält Adressverschiebungen

**Einordnung:** Abweichung des Plans von der Herstellerdokumentation.

Die Tabelle vermischt Registerbezeichnungen und tatsächliche Telegrammadressen. Korrektur:

| Messwert | Registerbezeichnung | Adresse im Telegramm |
|---|---|---|
| Spannungen L1–L3 | 30109–30114 | 108–113 |
| Ströme L1–L3 | 30115–30120 | 114–119 |
| Gesamtleistung | 30121–30122 | 120–121 |
| Gesamtenergie | 30129–30130 | 128–129 |
| Sitzungsenergie | 30133–30134 | 132–133 |
| Phasenflags | 30206 | 205 |

`PHASES` liefert eine Bitmaske. Die Schreibregister 40300, 40333 und 40338 entsprechen den
Telegrammadressen 299, 332 und 337. Funktion 16 und flüchtige Stromvorgaben sind richtig gewählt.
Phasenmodus ist ab Firmware 55.5, Force-State ab 55.6 dokumentiert. Firmware 60.3 hatte einen
Byte-Reihenfolgefehler, laut Dokumentation behoben mit 60.4.

Quelle: [go-e Modbus-Dokumentation](https://github.com/goecharger/go-eCharger-API-v2/blob/main/modbus-de.md).

**Empfehlung:** Für jedes Adapterfeld Adresse, Länge, Datentyp, Byte-/Wortreihenfolge und
Umrechnung festhalten. Tests müssen unabhängige Rohdatenbeispiele verwenden, damit eine falsche
Adresskonstante nicht in Test und Implementierung gleichermaßen bestätigt wird.

### T-03 — Kritisch: Notabschaltung und Bridge-Pause widersprechen sich

**Einordnung:** Vertragswiderspruch und unvollständiger Ablauf.

Die Bridge-Pause unterbindet automatische Sollwertübersetzung. Die Zuständigkeitstabelle
verspricht zugleich, HEMS-Notabschaltung über `0 A` sicher an der Wallbox umzusetzen. Bei
pausierter Bridge ist beides ohne weitere Regel nicht gleichzeitig erfüllt.

Während eines Phasenwechsels sollen neue Vorgaben außerdem gesammelt werden. Ein Stopp darf
jedoch nicht bis zum Ende einer normalen Umschaltsequenz warten. Ein veralteter positiver
Befehl darf nach Eingang des Stopps nicht mehr ausgeführt werden.

**Empfehlung:** Stoppvorrang, Befehlsverwerfung, maximale Reaktionszeit und Verhalten bei Pause
explizit spezifizieren. Transportzugriffe serialisieren, aber keine lange Bestätigungswartezeit
unter einer Sperre halten, die auch den Stopppfad blockiert. Vor erneuter Freigabe die aktuelle
Vorgabe und gegebenenfalls die Notabschaltung nochmals prüfen.

### T-04 — Hoch: Phasenbestätigung bei offenem Schütz ist nicht beschrieben

**Einordnung:** Technische Ablaufhürde; Hardwareverhalten noch zu prüfen.

Der Entwurf wartet auf die tatsächlich aktiven Phasen hinter dem Schütz, bevor der neue
Stromsollwert angewendet wird. Ohne Fahrzeug, vor dem Ladestart oder bei fehlender Autorisierung
kann das Schütz offen sein. Dann lässt sich eine gewünschte aktive Phasenzahl noch nicht auf
diese Weise bestätigen.

**Folge:** Der Ablauf kann unnötig in einen Timeout laufen oder den Ladestart verhindern.

**Empfehlung:** Konfigurierten Phasenmodus, angeforderten Modus und tatsächlich aktive Phasen
getrennt behandeln. Eigene Abläufe für Vorbereitung im Stillstand, Ladestart und Wechsel während
des Ladens definieren. Ein zulässiger Zustand ohne aktive Phasen darf nicht pauschal als Fehler
gelten. „Sicherer Übergangswert“, Timeout und Fehlerreaktion brauchen konkrete Definitionen.

Die exakte Zuordnung der go-e-Phasenmoduswerte bleibt wie im Plan vorgesehen vor Freigabe an
der Zielhardware zu bestätigen und mit Firmwarebezug zu dokumentieren.

### T-05 — Hoch: Debounce stellt keine gemeinsame Transaktion her

**Einordnung:** Grenze des vorgesehenen Interfaces.

Ein kurzes Bündelungsfenster ordnet zwei Helferänderungen nicht zuverlässig derselben
HEMS-Regelentscheidung zu. Der HA-Client schreibt sequenziell und verwendet pro Aufruf einen
Timeout von fünf Sekunden. Ein Aufruf kann erfolgreich sein und der andere scheitern.

Ein gleichzeitig gelesener HA-Zustand ist daher zwar ein Schnappschuss, aber nicht zwingend ein
zusammengehöriger Strom-/Phasenauftrag.

**Empfehlung:** Gemeinsamen Auftrag oder gemeinsame Revision prüfen. Bei Beibehaltung der
separaten Helfer müssen Zwischenzustände und Teilfehler ausdrücklich behandelt werden. Eine
längere Debounce-Zeit allein liefert keine Transaktionsgarantie.

Codebezug: [ha_client.py](../SkytechHEMS/app/ha_client.py), `execute_write_ops()`.

### T-06 — Hoch: Ausfallerkennung und Wiederholung sind unvollständig

**Einordnung:** Fehlende Betriebsregeln und bestehendes HEMS-Verhalten.

| Fall | Bestehende Lücke |
|---|---|
| HEMS steht, HA läuft | Ein alter positiver Helferwert kann unbegrenzt bestehen bleiben. |
| Helferwert bleibt lange unverändert | Das kann normaler Betrieb sein; Änderungsalter ist kein Lebenszeichen. |
| Provider-Sensor wird nicht verfügbar | HEMS verwendet bei ungültiger Istleistung intern 0 W und sperrt das Gerät dadurch nicht automatisch. |
| Schreiben schlägt fehl, Lesen funktioniert | Der Fehler muss unabhängig vom erfolgreichen Poll sichtbar bleiben; erneuter Versuch darf nicht von einer neuen Helferänderung abhängen. |
| Verbindung fällt vollständig aus | Der Provider kann keinen neuen Stoppbefehl zustellen; reine Softwareabsicht garantiert dann keinen physischen Stopp. |
| HA oder Provider startet neu | Wiederhergestellte Helfer können alte positive Anforderungen enthalten. |

**Empfehlung:** HEMS-Ausfall, Gerätekommunikationsfehler und ungültige Befehle getrennt behandeln.
Wiederholungen mit begrenzter Frequenz, aktuellem Schnappschuss und Vorrang für Stopp festlegen.
Für einen garantierten Stopp bei Verbindungsverlust wäre eine geräteseitige Ausfallfunktion
erforderlich; deren Verfügbarkeit ist bisher nicht nachgewiesen.

Codebezug: [devices.py](../SkytechHEMS/app/ems/devices.py), `update_from_ha()`;
[Geräteklasse controllable](../SkytechHEMS/docs/device_classes/controllable.md).

### T-07 — Mittel: Feste Phasenzahl ist für den Provider nicht erkennbar

**Einordnung:** Konfigurationslücke.

Bei HEMS `phases: "1"` oder `"3"` gibt es keinen verpflichtenden Phasenhelfer. Der Provider
bekommt bisher nur `hems_entity_prefix` und kennt die HEMS-Gerätekonfiguration nicht.

**Empfehlung:** Feste Phasenzahl beziehungsweise automatische Umschaltung als explizite
Provider-Konfiguration definieren. Fehlender optionaler Helfer und ausgefallener verpflichtender
Helfer müssen unterscheidbar sein.

### T-08 — Mittel: Freigabepolitik und RFID-Zusammenspiel sind offen

**Einordnung:** Fehlende fachliche Festlegung und Hardwareprüfung.

Der Entwurf verweist auf eine „konfigurierte Steuerpolitik“, definiert aber weder deren Optionen
noch den Standard. go-e unterscheidet bei `frc` Neutral, Aus und Ein. Aus der bloßen Bestätigung
eines Schreibzugriffs folgt noch keine Aussage darüber, ob Zugangskontrolle, Fahrzeug und
Ladelogik den Ladevorgang zulassen.

**Empfehlung:** Positive Freigabe, Rücknahme der Freigabe und Erhalt der Autorisierung getrennt
festlegen. RFID-Einstellungen unverändert zu lassen genügt allein noch nicht als Nachweis, dass
die gewählte Befehlsfolge keine Autorisierung umgeht oder verliert.

Quelle: [go-e API-Keys](https://github.com/goecharger/go-eCharger-API-v2/blob/main/API_KEYS_FIRMWARE/apikeys-de.md).

### T-09 — Mittel: Geräteidentität und Entity-Namen brauchen klare Regeln

**Einordnung:** Fehlende Integrationsdetails.

Ein Anzeigename eignet sich zur Benennung, aber nicht als stabile Geräteidentität. HA verwendet
stabile Unique IDs und eine Entity Registry; tatsächlich vorhandene Entity-IDs können von
Beispielnamen abweichen. Die Config-Flow-Dokumentation nennt etwa Seriennummern als geeignete
Identität und schließt IP-Adresse sowie Gerätename als stabile Unique ID aus.

**Empfehlung:** Stabile Geräte-/Entity-IDs, Schutz gegen doppelte Einrichtung und Verhalten bei
Umbenennung festlegen. HEMS-Konfiguration auf die tatsächlich vorhandenen Entity-IDs beziehen.
Auch zwei aktive Provider-Zuordnungen zum selben HEMS-Präfix sollten erkannt werden.

Quellen: [HA Config Flow](https://developers.home-assistant.io/docs/core/integration/config_flow/),
[HA Entity Registry](https://developers.home-assistant.io/docs/entity_registry_index/).

## 4. Allgemeine Informationen und Empfehlungen

### Architektur beibehalten

- HEMS bleibt für Überschuss, Prioritäten und Sollwertbildung zuständig.
- Der Provider übernimmt Geräteprotokoll, Befehlsausführung und gerätespezifische Schutzabläufe.
- Herstellerdetails bleiben im Adapter.
- Der Provider schreibt keine HEMS-Sollwerthelfer zurück.
- Messwert, angeforderter Wert, bestätigter Schreibauftrag und tatsächlicher Betriebszustand
  bleiben unterscheidbar.
- Fehlende Messwerte werden nicht als echte Nullwerte veröffentlicht.

### Zustandsmaschine konkretisieren

Vor der Steuerungsimplementierung sollten mindestens Stillstand, Startvorbereitung, Laden,
Phasenwechsel, Stopp, Kommunikationsfehler und Wiederanlauf beschrieben werden. Für jeden
Übergang sind Voraussetzungen, zulässige Befehle, Bestätigung, Timeout und Fehlerreaktion
festzulegen. Ein neuer Stopp muss einen älteren positiven Auftrag überholen können.

Auch die HEMS-Umschaltsperre ist keine vollständige geräteseitige Schutzgarantie: Im vorhandenen
Code gilt sie nicht gleichermaßen für jeden Ladestart; der interne Umschaltzeitstempel überlebt
keinen HEMS-Neustart. Die Aussage, allein HEMS verhindere jedes Flattern, sollte deshalb
eingeschränkt und anhand der erforderlichen Geräteschutzzeiten geprüft werden.

### Datenmodell und Diagnose vervollständigen

Die normalisierten Status- und Fehlerwerte brauchen definierte Wertebereiche und einen Umgang
mit unbekannten Herstellerwerten. Kommunikationsfehler, ungültige HEMS-Vorgaben,
Phasenwechsel-Timeouts und echte Gerätefehler sollten unterscheidbar sein. Ein erfolgreicher
Poll darf einen weiterhin bestehenden Schreibfehler nicht löschen.

Das spätere Adaptermodell sollte seine Fähigkeiten explizit bereitstellen: unterstützte
Phasenbetriebsarten, Stromgrenzen und Möglichkeiten zur Befehlsbestätigung. Das erleichtert
weitere Hersteller, ohne im generischen Coordinator Sonderfälle zu verteilen.

### Vertrag und Plan gemeinsam pflegen

Nach Beantwortung der Fragen sind der Umsetzungsplan und beide Vertragskopien im selben
Arbeitspaket zu überarbeiten. Ein automatischer Vergleich der Kopien ist sinnvoll. Der Vertrag
sollte die gemeinsamen Zusagen enthalten; Registerdetails bleiben im Provider-Plan beziehungsweise
in der Adapterdokumentation.

## 5. Prüfnachweise und zusätzlich erforderliche Tests

Bei der Prüfung liefen die vorhandenen HEMS-Tests mit folgendem Aufruf erfolgreich:

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_controllable_device.py tests/test_emergency.py
```

**Ergebnis:** 108 Tests bestanden. Der Aufruf erfolgte im Verzeichnis `SkytechHEMS`.

Der Fehler T-01 wurde zusätzlich über einen vollständigen Regelzyklus reproduziert; er wird von
diesen vorhandenen Tests nicht abgedeckt. Es wurde noch kein dauerhafter Regressionstest ergänzt.
Eine Prüfung an echter Wallbox-Hardware erfolgte nicht. Die Prüfung ist keine Freigabe für
produktiven Betrieb.

Zusätzlich zum bestehenden Testplan sollten mindestens diese Fälle aufgenommen werden:

- Reproduktion T-01 und beide Umschaltrichtungen unter Rampe und Totband.
- Nur Phasenänderung, nur Stromänderung und verzögerte oder fehlgeschlagene zweite Helferänderung.
- `0 A` während jeder Phase eines laufenden Wechsels; kein späterer positiver Altbefehl.
- Bridge-Pause und Notabschaltung gemäß der noch zu treffenden Entscheidung.
- Start ohne Fahrzeug, mit offenem Schütz, mit fehlender RFID-Freigabe und nach Ladeende.
- Ausfall nur des HEMS, nur des Schreibzugriffs und der gesamten Geräteverbindung.
- Wiederholung eines fehlgeschlagenen Befehls ohne weitere Helferänderung.
- Neustart mit altem positivem Sollwert sowie mit vorher pausierter Bridge.
- Feste Ein- und Dreiphasenkonfiguration und fehlender verpflichtender Phasenhelfer.
- Doppelte Geräteeinrichtung, umbenannte Entities und doppelt verwendetes HEMS-Präfix.
- Unabhängige Modbus-Rohdatenfälle für Adressen, Umrechnungen und Phasenflags.

## 6. Empfohlene Reihenfolge der nächsten Schritte

1. Fragen F-01 bis F-12 beantworten; insbesondere Hardware, Ausfall- und Abschaltpolitik festlegen.
2. Registertabelle korrigieren und getestete Firmware-/Gerätegrenzen definieren.
3. HEMS-Fehler T-01 beheben und mit einem Regressionstest absichern.
4. Befehlsübergabe und Zustandsmaschine einschließlich Stoppvorrang konkretisieren.
5. Plan und beide Vertragskopien konsistent aktualisieren.
6. Provider zunächst lesend, anschließend mit fester Phasenzahl und danach mit Phasenwechsel testen.
7. Hardware-Abnahme dokumentieren und erst danach den geprüften Umfang freigeben.
