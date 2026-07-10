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
from typing import TYPE_CHECKING

import serial

from ..base import DeviceNotPresentError, TransportError

if TYPE_CHECKING:
    from collections.abc import Callable

_TX_TERMINATOR = b"\n\r"
_RX_TERMINATOR = b"\r"
_DRAIN_DELAY_S = 0.02
_ENCODING = "ascii"

DEFAULT_BAUDRATE = 9600
DEFAULT_TIMEOUT_S = 1.0


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
    """One request/reply cycle using the proven recipe.

    The buffer reset before the write discards stale or echoed bytes left
    over from the previous exchange; the post-terminator drain captures
    the stray bytes the device trails after its first CR. An empty read
    is pyserial's timeout signal: no response arrived.
    """
    try:
        ser.reset_input_buffer()
        ser.write(command.encode(_ENCODING) + _TX_TERMINATOR)
        ser.flush()
        data = ser.read_until(_RX_TERMINATOR)
        time.sleep(_DRAIN_DELAY_S)
        bytes_waiting = ser.in_waiting
        if bytes_waiting:
            data += ser.read(bytes_waiting)
    except serial.SerialException as exc:
        raise TransportError(f"serial I/O failed for {command!r}: {exc}") from exc
    response = data.decode(_ENCODING, errors="replace").strip()
    if not response and require_response:
        raise TransportError(f"no response to {command!r} within {ser.timeout}s")
    return response


def close_quietly(port: serial.Serial) -> None:
    """Best-effort close for teardown paths.

    SerialException subclasses OSError, so a failing pyserial close is
    swallowed instead of surfacing from cleanup.
    """
    try:
        port.close()
    except OSError:
        pass
