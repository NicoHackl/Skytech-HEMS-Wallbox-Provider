"""Normalisiertes Datenmodell einer Wallbox — herstellerunabhängig.

`None` bedeutet immer „nicht verfügbar", `0` ist ein echter Messwert (Vertrag: ein fehlender
Messwert ist nicht `0`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# Normalisierte Werte von `vehicle_state` (Sensor „Wallbox-Status").
VEHICLE_STATES = (
    "unbekannt",
    "bereit",
    "laedt",
    "wartet_auf_fahrzeug",
    "ladung_beendet",
    "fehler",
)

# Normalisierte Werte von `fault` (Sensor „Fehler"). „kein_fehler" ist ein expliziter Zustand.
FAULTS = (
    "kein_fehler",
    "fehlerstrom",
    "phasenfehler",
    "ueberspannung",
    "ueberstrom",
    "erdung",
    "schuetz",
    "uebertemperatur",
    "kabelverriegelung",
    "sonstiger_fehler",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class WallboxState:
    """Ein Messwert-Schnappschuss der Wallbox."""

    charging_power_w: float | None
    voltage_l1_v: float | None
    voltage_l2_v: float | None
    voltage_l3_v: float | None
    current_l1_a: float | None
    current_l2_a: float | None
    current_l3_a: float | None
    active_phase_count: int | None
    vehicle_state: str | None
    vehicle_connected: bool | None
    is_charging: bool | None
    fault: str | None
    session_energy_wh: float | None
    total_energy_wh: float | None
    max_current_a: int | None
    available: bool
    last_update: datetime
