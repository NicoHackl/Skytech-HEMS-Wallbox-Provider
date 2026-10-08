"""Gemeinsamer Vertrag aller Wallbox-Adapter.

Coordinator, HEMS-Anbindung und Platforms kennen ausschließlich dieses Protocol, nie
Herstellerdetails (docs/architektur.md, Invariante 1). Register, Skalierungen und Fehlercodes
bleiben im jeweiligen Adapter.
"""

from __future__ import annotations

from typing import Protocol

from ..models import WallboxState


class WallboxAdapterError(Exception):
    """Ein Adapter-Aufruf ist fehlgeschlagen (Transport, Antwort, Gerät)."""


class WallboxFirmwareError(WallboxAdapterError):
    """Die Firmware des Geräts unterstützt die benötigten Funktionen nicht oder ist fehlerhaft."""


class WallboxAdapter(Protocol):
    """Protocol, das jeder Wallbox-Adapter implementiert."""

    # Kleinster positiver Ladestrom in A, den das Gerät annimmt (IEC 61851: 6 A).
    min_current_a: int

    async def connect(self) -> None:
        """Verbindung aufbauen. Wirft `WallboxAdapterError`, wenn das Gerät nicht erreichbar ist."""
        ...

    async def identify(self) -> tuple[str, str]:
        """(Seriennummer, Firmware) lesen und die Firmware prüfen.

        Wirft `WallboxFirmwareError` bei nicht unterstützter Firmware.
        """
        ...

    async def read(self) -> WallboxState:
        """Aktuellen Zustand lesen. Wirft `WallboxAdapterError`, nie einen erratenen Ersatzwert."""
        ...

    async def set_current(self, current_a: int) -> None:
        """Ladestrom flüchtig setzen (ganze A, ≥ `min_current_a`)."""
        ...

    async def set_phases(self, phases: int) -> None:
        """Phasenzahl 1 oder 3 anfordern."""
        ...

    async def allow_charging(self, allowed: bool) -> None:
        """Ladefreigabe erteilen (`True`) oder zurücknehmen (`False`)."""
        ...

    async def close(self) -> None:
        """Transport schließen."""
        ...
