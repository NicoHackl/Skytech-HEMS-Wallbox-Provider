# D-003 — Befehlsfolge an die Wallbox

**Datum:** 07.10.2026 · **Status:** Aktiv

## Kontext

Das HEMS schreibt Phasenzahl und Strom als zwei getrennte Helfer, ohne Transaktion. Die go-e
Gemini kennt Strom (flüchtig, Register 299), Phasenmodus (`psm`, Register 332) und Freigabe
(`frc`, Register 337). Eine Bestätigung der aktiven Phasen ist bei offenem Schütz (kein Fahrzeug,
vor Ladestart) nicht möglich.

## Entscheidung

- Stopp: nur `frc` = 1 (Aus); der gespeicherte Strom bleibt.
- Positiv: Phasenmodus (nur bei `automatisch` und nur, wenn er vom zuletzt erfolgreich
  geschriebenen abweicht) → Strom → `frc` = 2 (Ein). Ohne Zwischenwert und ohne Bestätigung.
- Vor jedem positiven Schritt wird der wirksame Sollwert neu gebildet; weicht er ab, wird
  abgebrochen und mit dem neuesten Wert neu begonnen. Folgen laufen nie parallel.
- Alle `keepalive_s` (Standard 30 s) wird der wirksame Sollwert erneut geschrieben — auch nach
  einem Fehler; so heilt ein Teilfehler (Phase geschrieben, Strom nicht) spätestens nach einem Takt.

## Folgen

- Zwischen Phasen- und Stromschritt kann kurz der alte Strom mit der neuen Phasenzahl anliegen
  (Vertrag: bekannte Grenze).
- `frc` = 2 lässt das Laden unabhängig von RFID zu; V1 setzt deaktiviertes RFID voraus.
