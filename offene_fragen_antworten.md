# Offene Fragen — Wallbox Provider V1

**Dokumentstand:** 07.10.2026
**Zweck:** Alle Entscheidungen, die vor der Implementierung fehlen. Bitte jeweils unter **Antwort:** eintragen.
**Quellen:** [review_open_questions.md](review_open_questions.md), [plan_v1.md](plan_v1.md),
[Vertrag](contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md)

Kürzel `T-xx` verweisen auf die technischen Befunde in `review_open_questions.md`.
„Empfehlung" ist ein Vorschlag, keine getroffene Entscheidung. Leer lassen = offen.

---

## A. Hardware und Installation

### F-01 — Welche Hardware wird eingesetzt?
- Modell: Gemini oder Gemini 2.0, ggf. flex? Leistungsvariante?
- Installierte Firmware? (Phasenmodus ab 55.5, Force-State ab 55.6; 60.3 hat Byte-Order-Fehler, behoben in 60.4)
- Welche Fahrzeuge laden?
- Dreiphasiger Anschluss? Abweichende installierte Strombegrenzung?
- Stehen Wallbox und Fahrzeug für wiederholte Hardwaretests zur Verfügung?

**Antwort:**
Gemini, alles andere vorerst "normal" nehmen

### F-02 — RFID / Zugangskontrolle
Wird RFID genutzt oder ist die Wallbox frei zugänglich? Soll eine vorhandene Autorisierung über
PV-Ladepausen und Phasenwechsel erhalten bleiben?

**Antwort:**
RFID möchte ich in zukünftigen Version als optional mitnutzen wenn ich darauf freie aktion in HA legen kann, also das ich über die wallboxschnittstelle bekomme wenn und welcher rfid gerade erkannt wird

### F-03 — Bestehende Steuerungen
Gibt es go-e-App-Zeitpläne, PV-Steuerung, go-e Controller, OCPP oder HA-Automationen, die
Ladestrom, Phasenmodus oder Freigabe verändern? Welche sollen weiterlaufen?

**Antwort:**
Keine externe oder andere Steuerung nur HEMS

---

## B. Auslieferung und Umfang

### F-04 — Custom-Integration oder Supervisor-Add-on?
Plan: HA-Custom-Integration mit Config Flow, Auslieferung per HACS.
**Empfehlung:** Custom-Integration wie im Plan.

**Antwort:**
Custom integration wie battery-provider

### F-05 — HEMS-Änderungen erlaubt?
- Darf der HEMS-Bug T-01 (Phasenwechsel schreibt keinen Strom, Totband/Rampe) im Rahmen dieses
  Vorhabens behoben werden?
- Sind kleine Vertragserweiterungen erlaubt (gemeinsamer Auftrag, Lebenszeichen, Rückmeldung)?
- Alternative: erste Freigabe nur mit fester Phasenzahl, T-01 später.

**Empfehlung:** T-01 vor Freigabe automatischer Phasenwechsel beheben; Ausschluss von
HEMS-Änderungen im Plan streichen.

**Antwort:**
ja all das nötige darf angepasst werden

### F-06 — Manuelle Steuerung ohne HEMS
Der Vertrag sieht bei leerem `hems_entity_prefix` nur einen Entity-Lieferanten vor, erwähnt aber
manuelle Befehle. Soll der Provider eigene Bedienelemente für Strom, Phasen und Freigabe bieten?
Wie wird bei manueller Bedienung die Kontrolle zurück ans HEMS gegeben?

**Antwort:**
es soll wie beim battery-provider einen schalter "HEMS Steuerung" geben und wenn "manuell" ist dann über die entitäten die du beschrieben hast

---

## C. Abschaltung, Ausfälle, Wiederanlauf

### F-07 — HEMS fällt aus, HA läuft weiter
Mit letztem Sollwert weiterladen, oder nach Frist stoppen? Welche Frist?
**Empfehlung:** Bei gewünschtem Stopp ein separates HEMS-Lebenszeichen im Vertrag ergänzen; das
Alter einer Sollwertänderung erkennt keinen Ausfall.

**Antwort:**
Ja wir nehmen das lebenszeichen vom HEMS in richtung provider, und dabei es für beide wallbox und battery
Rückfrage 07.10.2026: HEMS veröffentlicht einen Status-Helfer mit allgemeinen Werten als Attribute (wie bei der Powerflow-Card). Beide Verträge (Wallbox und Battery) jetzt im selben Arbeitspaket.

### F-08 — Notabschaltung bei pausierter Bridge
Soll die HEMS-Notabschaltung die Bridge-Pause übersteuern, auch bei manuellem Betrieb?
**Empfehlung:** Ausdrücklich definieren. Dafür muss der Provider Notabschaltung und normales
`0 A` unterscheiden können (Stromwert allein reicht nicht → Vertragserweiterung).

**Antwort:**
Nein

### F-09 — Reaktionszeit und Fehlerquittierung
- Maximale Zeit bis Stopp bei erreichbarer Wallbox?
- Nach fehlgeschlagenem Phasenwechsel: automatisch neu starten oder erst nach Quittierung?
- Verhalten nach vorübergehender Kommunikationsstörung?

**Empfehlung:** Stopp vor positiven Befehlen priorisieren; Kommunikationsfehler und
Phasenwechsel-Fehler getrennt behandeln; Fristen nach Hardwaretest festlegen.

**Antwort:**
Immer wieder normal weitermachen/laden beginnen

### F-10 — Verhalten nach Neustart
- Soll eine bewusst pausierte Bridge nach Neustart automatisch wieder aktiv werden?
- Darf ein wiederhergestellter positiver HEMS-Wert sofort einen Ladestart auslösen, oder erst
  nach nachgewiesenem frischem HEMS-Zyklus?

**Antwort:**
Ja und nach frischem HEMS Zyklus

---

## D. Phasenbetrieb und Betriebsgrenzen

### F-11 — Welche Phasenbetriebsarten in V1?
Nur automatisch 1↔3 Phasen, oder zusätzlich feste 1- bzw. 3-phasige Konfiguration? Wie wird die
feste Einstellung im Provider konfiguriert (T-07)?
**Empfehlung:** Feste Phasenzahl und automatische Umschaltung als explizite Provider-Konfiguration;
nie aus einem fehlenden Helfer auf die Phasenzahl schließen.

**Antwort:**
die empfehlung übernehmen

### F-12 — Priorität: Ladeunterbrechungen vs. Fehlerabschaltung
Ist „keine zusätzlichen Stop/Start-Zyklen" nur Ziel im erfolgreichen Normalablauf, mit Stopp bei
Fehlern immer erlaubt? Bekannte Fahrzeug-Einschränkungen bei Ladepausen oder Phasenwechseln?
**Empfehlung:** Komfortziel nur für den Normalablauf; Fehlerstopp hat Vorrang.

**Antwort:**
Ja empfehlung übernehmen

---

## E. Entscheidungen aus den technischen Befunden

### E-01 — Phasenwechsel bei offenem Schütz (T-04)
Ohne Fahrzeug, vor Ladestart oder ohne Autorisierung lassen sich aktive Phasen nicht bestätigen.
Zu entscheiden:
- Eigene Abläufe für (a) Vorbereitung im Stillstand, (b) Ladestart, (c) Wechsel während des Ladens?
- Welcher Wert ist der „sichere Übergangswert" (z. B. technisches Minimum 6 A)?
- Welcher Timeout für die Phasenbestätigung?
- Reaktion bei Timeout (Stopp, Rückfall auf letzte Phasenzahl, Quittierung)?

**Antwort:**
Einfach durchreichen (Phasenmodus setzen, danach sofort Strom; kein Übergangswert, keine Bestätigung).
Rückfrage 07.10.2026: Umschaltung kann nur der Provider ausführen, weil das HEMS nie auf Hardware zugreift.

### E-02 — Strom und Phase als gemeinsamer Auftrag (T-05)
Zwei getrennte Helfer sind keine Transaktion. Optionen:
1. Gemeinsame Revision/Auftrags-ID im Vertrag (HEMS-Änderung).
2. Getrennte Helfer behalten, Zwischenzustände und Teilfehler im Provider regeln.

**Empfehlung:** Option 2 nur, wenn T-01 behoben ist und Teilfehler im Vertrag stehen; sonst 1.

**Antwort:**
Ja varainte 2

### E-03 — Freigabepolitik und RFID (T-08)
go-e `frc`: Neutral / Aus / Ein. Zu entscheiden:
- Welcher `frc`-Wert bei positivem Sollwert? Welcher bei `0 A`?
- Wie bleibt die RFID-Autorisierung erhalten (Hardwaretest vor Produktivbetrieb)?
- Was heißt „konfigurierte Steuerpolitik" konkret, welche Optionen, welcher Standard?

**Antwort:**
Bei reiner HEMS regelung nehmen wir laden = 2 und 0A bzw. nicht laden = 1

### E-04 — Wiederholung fehlgeschlagener Befehle (T-06)
Nach Schreibfehler ohne neue Helferänderung erneut versuchen? Wie oft / in welchem Abstand?
Soll der Fehler sichtbar bleiben, bis ein Schreibvorgang gelingt (auch wenn Polls erfolgreich sind)?

**Antwort:**
Wenn die wallbox nicht "default" auf 0A geht wenn länger kein neuer wert kommt alle 30s
Rückfrage 07.10.2026: Sollwert alle 30 s erneut schreiben, Intervall konfigurierbar.

### E-05 — Provider-Sensor nicht verfügbar (T-06)
HEMS rechnet bei ungültiger Istleistung intern mit 0 W und sperrt das Gerät nicht. Soll das im HEMS
geändert werden (Gerät sperren), oder bleibt es bekannte Grenze?

**Antwort:**
Mach es so wie es beim Battery-provider ist

### E-06 — Gerätenahe Ausfallfunktion (T-06)
Bei vollständigem Verbindungsverlust kann der Provider keinen Stopp mehr senden. Soll geprüft
werden, ob die Wallbox eine eigene Ausfallfunktion (Fail-safe/Timeout) bietet? Wenn nicht: Ist
„kein garantierter Stopp bei Verbindungsverlust" als dokumentierte Grenze akzeptabel?

**Antwort:**
ja ist akzeptabel

### E-07 — Geräteidentität und Duplikate (T-09)
- Stabile Unique ID aus Seriennummer statt Anzeigename/IP?
- Verhalten bei Umbenennung von Entities?
- Zwei Provider-Instanzen auf demselben `hems_entity_prefix` blockieren?

**Empfehlung:** Seriennummer als Unique ID; doppelte Zuordnung im Config Flow ablehnen.

**Antwort:**
Das ist dem user überlassen das er das richtig pflegen kann

---

## F. Vertragsmängel zur Klärung

### V-01 — Parameternamen
- Vertrag nennt `min_umschaltzeit_s`, die Beispielkonfiguration `phase_switch_delay_s`. Welcher Name
  ist richtig? (noch nicht gegen HEMS-Code geprüft)
- `min_current_a..max_current_a` ist nicht definiert; HEMS verwendet `technical_minimum` /
  `technical_maximum`. Vertrag auf die HEMS-Namen angleichen?

**Antwort:**
ja

### V-02 — Status je Vertragspunkt
Der Vertrag trägt nur „Entwurf für V1". Soll je Abschnitt ein Status (implementiert / bekannte
Grenze / Entwurf) gepflegt werden, wie in Regel 4 gefordert?

**Antwort:**
ja

### V-03 — Kürzung der Registerdetails
Registertabelle (T-02, Adresse = Register − 30001) bleibt im Provider-Plan, nicht im Vertrag?
**Empfehlung:** Ja; Vertrag enthält nur gemeinsame Zusagen.

**Antwort:**
ja

---

## G. Freigabe

### G-01 — Vorgehen und Reihenfolge
Zustimmung zur Reihenfolge: Fragen klären → T-01 im HEMS beheben → Zustandsmaschine und
Lebenszeichen spezifizieren → Plan und beide Vertragskopien aktualisieren → Provider lesend →
feste Phasenzahl → Phasenwechsel → Hardware-Abnahme?

**Antwort:**
passt so
