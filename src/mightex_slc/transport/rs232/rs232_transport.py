# ------------------------------------------------------------------------------
#  Filename: rs232_transport.py
#
#  Purpose: Real serial backend over pyserial, using the rs232 codec.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""The real hardware backend, implementing the transport interface over pyserial.

It opens the serial port, sends commands encoded by the rs232 codec, and
reads and decodes the replies.

The port is always explicit and the backend never scans or probes for one.
Opening a port is side-effecting (ECHOOFF enters PC Mode on MA/CA modules),
so only the port the caller names is ever touched; an unspecified port fails
the open.

Sharing one physical port is not supported. On POSIX the open takes exclusive
OS ownership (Windows ports are already exclusive at the OS open), and a port
held elsewhere surfaces as DeviceNotPresentError.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import serial

from ..base import (
    DeviceNotPresentError,
    InvalidHandleError,
    Transport,
    TransportError,
    TransportHandle,
    TransportOpenResult,
)
from . import codec

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from ...contract import OperatingMode

# The proven serial recipe, hardware-verified by the predecessor project
# (device_and_protocol.md §9): commands end in LF+CR, deliberately not the
# conventional CRLF; responses are read to the first CR and then drained
# briefly, because the device trails stray line-ending bytes after its
# terminator.
_TX_TERMINATOR = b"\n\r"
_RX_TERMINATOR = b"\r"
_DRAIN_DELAY_S = 0.02
_ENCODING = "ascii"
_DEFAULT_BAUDRATE = 9600
_DEFAULT_TIMEOUT_S = 1.0


def _close_quietly(port: serial.Serial) -> None:
    """Best-effort close for teardown paths.

    SerialException subclasses OSError, so a failing pyserial close is
    swallowed instead of surfacing from cleanup.
    """
    try:
        port.close()
    except OSError:
        pass


class _RS232Handle(TransportHandle):
    """The transport handle payload: the open pyserial port."""

    def __init__(self, port: serial.Serial) -> None:
        self.port = port


class RS232Transport(Transport):
    """The real serial backend: one instance owns one physical port.

    A single handle is active at a time; opening again before close fails
    rather than multiplexing the port.
    """

    def __init__(
        self,
        *,
        baudrate: int = _DEFAULT_BAUDRATE,
        timeout: float = _DEFAULT_TIMEOUT_S,
        serial_factory: Callable[..., serial.Serial] = serial.Serial,
    ) -> None:
        # serial_factory is the test seam: production uses pyserial, tests
        # inject a scripted double without patching imports.
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial_factory = serial_factory
        self._handle: _RS232Handle | None = None

    def open_device(self, port: str | None = None) -> TransportOpenResult:
        if self._handle is not None:
            raise TransportError("device is already open")
        if port is None:
            raise TransportError("no serial port specified")
        serial_port = self._open_serial_port(port)
        try:
            serial_number, capabilities = self._identify_controller(serial_port, port)
        except BaseException:
            # BaseException on purpose: never leak a half-open port.
            _close_quietly(serial_port)
            raise
        self._handle = _RS232Handle(serial_port)
        return TransportOpenResult(
            handle=self._handle,
            serial_number=serial_number,
            capabilities=capabilities,
        )

    def configure_normal(
        self,
        handle: TransportHandle,
        channel: int,
        current_max_ma: float,
        current_set_ma: float,
    ) -> None:
        ser = self._require_open(handle)
        self._command_ack(ser, codec.encode_normal(channel, current_max_ma, current_set_ma))

    def set_active_mode(self, handle: TransportHandle, channel: int, mode: OperatingMode) -> None:
        ser = self._require_open(handle)
        self._command_ack(ser, codec.encode_mode(channel, mode))

    def close_device(self, handle: TransportHandle) -> None:
        # Idempotent by identity: only the currently open handle closes the
        # port; a stale handle is a no-op and never touches a newer session.
        if self._handle is None or handle is not self._handle:
            return
        # The server has already dropped the device_id; the close must not fail.
        _close_quietly(self._handle.port)
        self._handle = None

    def _open_serial_port(self, port: str) -> serial.Serial:
        """Open the OS-level port; failure here means no reachable device.

        POSIX ttys allow concurrent opens, so the open requests exclusive
        (flock) ownership there to keep two transports off one physical
        port. Windows ports are exclusive at the OS open already.
        """
        try:
            return self._serial_factory(
                port=port,
                baudrate=self._baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self._timeout,
                **({"exclusive": True} if os.name == "posix" else {}),
            )
        except serial.SerialException as exc:
            raise DeviceNotPresentError(f"cannot open {port}: {exc}") from exc

    def _identify_controller(self, serial_port: serial.Serial, port: str) -> tuple[Any, Any]:
        """Confirm a controller is answering and read its identity.

        ECHOOFF enters PC Mode on MA/CA modules (hygiene elsewhere) and
        never returns a clean ack, so its reply, possibly nothing, is
        consumed and ignored. DEVICEINFO then doubles as the presence
        probe, because an open tty proves nothing about a controller
        answering: silence maps to DeviceNotPresentError rather than
        _exchange's TransportError. Returns (serial_number, capabilities).
        """
        self._exchange(serial_port, codec.ECHO_OFF_COMMAND, require_response=False)
        response = self._exchange(serial_port, codec.DEVICE_INFO_COMMAND, require_response=False)
        if not response:
            raise DeviceNotPresentError(f"no response to DEVICEINFO at {port}")
        codec.check_response(response, codec.DEVICE_INFO_COMMAND)
        info = codec.parse_device_info(response)
        if info.module_number is None or info.serial_number is None:
            raise TransportError(f"DEVICEINFO did not identify the device: {response!r}")
        capabilities = codec.capabilities_for_module(info.module_number)
        return info.serial_number, capabilities

    def _require_open(self, handle: TransportHandle) -> serial.Serial:
        if self._handle is None or handle is not self._handle:
            raise InvalidHandleError("handle is not open")
        return self._handle.port

    def _command_ack(self, ser: serial.Serial, command: str) -> None:
        response = self._exchange(ser, command)
        codec.require_ack(response, command)

    def _exchange(
        self,
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
            raise TransportError(f"no response to {command!r} within {self._timeout}s")
        return response
