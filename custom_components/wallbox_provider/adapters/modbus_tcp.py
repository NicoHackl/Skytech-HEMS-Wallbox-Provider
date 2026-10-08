"""modbus_tcp.py — schlanker asynchroner Modbus-TCP-Client (Funktionen 3, 4 und 16).

Bewusst ohne Fremdbibliothek: der go-e-Adapter braucht nur drei Funktionen, und eine eigene
Implementierung hält die Integration frei von Versionskonflikten mit anderen HA-Integrationen,
die `pymodbus` in einer bestimmten Version mitbringen.

Jeder Aufruf ist eine vollständige Anfrage/Antwort unter einer Sperre — Lesen und Schreiben
teilen sich die Verbindung, laufen aber nie verschränkt (Vertrag: Transportzugriffe
serialisieren). Die Sperre gilt nur für **einen** Zugriff, nie für eine Befehlsfolge; ein Stopp
wartet so höchstens auf den gerade laufenden Einzelzugriff (siehe `hems_bridge.py`).

Fehler aller Art (Timeout, Verbindungsabbruch, Modbus-Exception-Antwort, kaputter Rahmen) werden
zu `ModbusError`. Nach einem Fehler wird die Verbindung verworfen und beim nächsten Aufruf neu
aufgebaut — ein toter Socket darf nicht still weiterleben (vgl. Battery-Provider D-013).
"""

from __future__ import annotations

import asyncio
import struct

FUNC_READ_HOLDING = 0x03
FUNC_READ_INPUT = 0x04
FUNC_WRITE_MULTIPLE = 0x10

_MBAP = struct.Struct(">HHHB")  # Transaction-ID, Protokoll-ID, Länge, Unit-ID


class ModbusError(Exception):
    """Eine Modbus-Anfrage ist fehlgeschlagen."""


class ModbusTcpClient:
    """Eine TCP-Verbindung zu einem Modbus-Gerät, serialisiert über eine Sperre."""

    def __init__(self, host: str, port: int, unit_id: int = 1, timeout: float = 3.0) -> None:
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._transaction_id = 0
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            await self._ensure_connected()

    async def close(self) -> None:
        async with self._lock:
            await self._drop()

    async def read_holding(self, address: int, count: int) -> list[int]:
        return await self._read(FUNC_READ_HOLDING, address, count)

    async def read_input(self, address: int, count: int) -> list[int]:
        return await self._read(FUNC_READ_INPUT, address, count)

    async def write_registers(self, address: int, values: list[int]) -> None:
        """Funktion 16 — auch für ein einzelnes Register (go-e unterstützt Funktion 6 nicht)."""
        if not values or len(values) > 123:
            raise ModbusError("Ungültige Registeranzahl")
        payload = struct.pack(">HHB", address, len(values), 2 * len(values))
        payload += b"".join(struct.pack(">H", v & 0xFFFF) for v in values)
        response = await self._request(FUNC_WRITE_MULTIPLE, payload)
        if len(response) != 4 or struct.unpack(">HH", response) != (address, len(values)):
            raise ModbusError("Unerwartete Schreibbestätigung")

    async def _read(self, function: int, address: int, count: int) -> list[int]:
        if not 1 <= count <= 125:
            raise ModbusError("Ungültige Registeranzahl")
        response = await self._request(function, struct.pack(">HH", address, count))
        if not response or response[0] != 2 * count or len(response) != 1 + 2 * count:
            raise ModbusError("Unerwartete Antwortlänge")
        return list(struct.unpack(f">{count}H", response[1:]))

    async def _request(self, function: int, payload: bytes) -> bytes:
        async with self._lock:
            try:
                await self._ensure_connected()
                assert self._reader is not None and self._writer is not None
                self._transaction_id = (self._transaction_id + 1) & 0xFFFF
                tid = self._transaction_id
                pdu = bytes([function]) + payload
                self._writer.write(_MBAP.pack(tid, 0, len(pdu) + 1, self._unit_id) + pdu)
                await asyncio.wait_for(self._writer.drain(), self._timeout)
                header = await asyncio.wait_for(
                    self._reader.readexactly(_MBAP.size), self._timeout
                )
                rtid, proto, length, _unit = _MBAP.unpack(header)
                if proto != 0 or length < 2 or length > 260:
                    raise ModbusError("Ungültiger Modbus-Rahmen")
                body = await asyncio.wait_for(self._reader.readexactly(length - 1), self._timeout)
                if rtid != tid:
                    raise ModbusError("Antwort gehört zu einer anderen Anfrage")
                if body[0] == function | 0x80:
                    code = body[1] if len(body) > 1 else 0
                    raise ModbusError(f"Modbus-Ausnahme {code}")
                if body[0] != function:
                    raise ModbusError("Antwort mit falscher Funktion")
                return body[1:]
            except ModbusError:
                await self._drop()
                raise
            except (TimeoutError, OSError, asyncio.IncompleteReadError) as exc:
                await self._drop()
                raise ModbusError(
                    f"Verbindung zu {self._host}:{self._port} fehlgeschlagen"
                ) from exc

    async def _ensure_connected(self) -> None:
        if self._writer is not None and not self._writer.is_closing():
            return
        await self._drop()
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), self._timeout
            )
        except (TimeoutError, OSError) as exc:
            raise ModbusError(f"Verbindung zu {self._host}:{self._port} fehlgeschlagen") from exc

    async def _drop(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None
        if writer is not None:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), 1.0)
            except (TimeoutError, OSError):
                pass
