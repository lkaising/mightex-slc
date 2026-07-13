# ------------------------------------------------------------------------------
#  Filename: serial_link.py
#
#  Purpose: Byte-level serial line discipline for the rs232 backend.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""The byte-level line discipline: the proven serial recipe, and nothing else.

Hardware-verified by the predecessor project (device_and_protocol.md §9):
commands end in LF+CR, deliberately not the conventional CRLF; responses are
read to the first CR and then drained briefly, because the device trails
stray line-ending bytes after its terminator. Everything here moves bytes
and maps serial failures to transport errors; what the strings mean is the
codec's business.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Final

import serial

from ..base import DeviceNotPresentError, TransportError

if TYPE_CHECKING:
    from collections.abc import Callable

DEFAULT_BAUDRATE: Final[int] = 9600
DEFAULT_TIMEOUT_S: Final[float] = 1.0

_ENCODING: Final[str] = "ascii"
_TX_TERMINATOR: Final[bytes] = b"\n\r"
_RX_TERMINATOR: Final[bytes] = b"\r"
_DRAIN_DELAY_S: Final[float] = 0.02

# Extended quiet-drain, for the multi-line responses (?TRIGP) where the first
# CR is not the end: keep reading until the line has been quiet for the
# window, hard-capped so a babbling device cannot hang the exchange. The
# 0.3 s window is the bench-proven capture recipe at 9600 baud.
_QUIET_WINDOW_S: Final[float] = 0.3
_QUIET_CAP_S: Final[float] = 3.0
_QUIET_POLL_S: Final[float] = 0.01


def open_serial_port(
    port: str,
    *,
    baudrate: int,
    timeout: float,
    serial_factory: Callable[..., serial.Serial],
) -> serial.Serial:
    """Open the OS-level serial port, requesting POSIX-exclusive access."""
    try:
        return serial_factory(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            **({"exclusive": True} if os.name == "posix" else {}),
        )
    except serial.SerialException as exc:
        raise DeviceNotPresentError(f"cannot open {port}: {exc}") from exc


def exchange(
    ser: serial.Serial,
    command: str,
    *,
    require_response: bool = True,
) -> str:
    """Send one command and return its drained, decoded response."""
    try:
        ser.reset_input_buffer()
        ser.write(command.encode(_ENCODING) + _TX_TERMINATOR)
        ser.flush()

        data = ser.read_until(_RX_TERMINATOR)
        time.sleep(_DRAIN_DELAY_S)
        if bytes_waiting := ser.in_waiting:
            data += ser.read(bytes_waiting)
    except serial.SerialException as exc:
        raise TransportError(f"serial I/O failed for {command!r}: {exc}") from exc

    response = data.decode(_ENCODING, errors="replace").strip()
    if require_response and not response:
        raise TransportError(f"no response to {command!r} within {ser.timeout}s")

    return response


def exchange_multiline(
    ser: serial.Serial,
    command: str,
    *,
    require_response: bool = True,
) -> str:
    """Send one command and capture its multi-line response.

    Same line discipline as exchange(), but the read keeps draining until the
    line has been quiet for a window instead of taking one post-CR drain —
    a multi-line response (?TRIGP) trickles in past the first CR slower than
    the single 20 ms drain can catch at 9600 baud. Costs the quiet window in
    latency on every call, which is why it is not the default exchange.
    """
    try:
        ser.reset_input_buffer()
        ser.write(command.encode(_ENCODING) + _TX_TERMINATOR)
        ser.flush()

        data = ser.read_until(_RX_TERMINATOR)
        data += _drain_until_quiet(ser)
    except serial.SerialException as exc:
        raise TransportError(f"serial I/O failed for {command!r}: {exc}") from exc

    response = data.decode(_ENCODING, errors="replace").strip()
    if require_response and not response:
        raise TransportError(f"no response to {command!r} within {ser.timeout}s")

    return response


def _drain_until_quiet(ser: serial.Serial) -> bytes:
    """Read until nothing new has arrived for the quiet window (hard-capped)."""
    data = bytearray()
    deadline = time.monotonic() + _QUIET_CAP_S
    quiet_since = time.monotonic()
    while time.monotonic() < deadline:
        if bytes_waiting := ser.in_waiting:
            data += ser.read(bytes_waiting)
            quiet_since = time.monotonic()
        elif time.monotonic() - quiet_since >= _QUIET_WINDOW_S:
            break
        else:
            time.sleep(_QUIET_POLL_S)
    return bytes(data)


def close_quietly(port: serial.Serial) -> None:
    """Close a serial port without surfacing cleanup errors."""
    try:
        port.close()
    except OSError:
        pass
