# ------------------------------------------------------------------------------
#  Filename: rs232_transport.py
#
#  Purpose: Real serial backend over pyserial, using the rs232 codec.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The real hardware backend, implementing the transport interface over pyserial.

It opens the serial port, sends commands encoded by the rs232 codec, and reads
and decodes the replies. The port is always explicit: open_device receives the
serial device path, and open_device(None) fails the open. This backend never
scans or probes ports — opening a port is side-effecting (ECHOOFF enters
PC Mode on MA/CA modules), so it opens only the one it is told to. This is the
file that touches an actual device. Sharing one physical port is not
supported: on POSIX the open takes exclusive OS ownership (Windows ports are
exclusive at the OS open already), and a port held elsewhere surfaces as
DeviceNotPresentError.
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

    from ...contract import OperatingMode

# The proven serial recipe, hardware-verified by the predecessor project
# (device_and_protocol.md §9): commands end LF+CR — deliberately not the
# conventional CRLF — while responses are read to the first CR and then
# drained briefly, because the device trails stray line-ending bytes after
# its terminator.
_TX_TERMINATOR = b"\n\r"
_RX_TERMINATOR = b"\r"
_DRAIN_DELAY_S = 0.02
_ENCODING = "ascii"
_DEFAULT_BAUDRATE = 9600
_DEFAULT_TIMEOUT_S = 1.0


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
        try:
            ser = self._serial_factory(
                port=port,
                baudrate=self._baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self._timeout,
                # POSIX ttys allow concurrent opens; exclusive (flock) closes
                # that hole so two transports cannot share one physical port.
                # Windows ports are exclusive at the OS open already.
                **({"exclusive": True} if os.name == "posix" else {}),
            )
        except serial.SerialException as exc:
            raise DeviceNotPresentError(f"cannot open {port}: {exc}") from exc
        try:
            # Enter host control. ECHOOFF is PC-Mode entry on MA/CA modules
            # and hygiene elsewhere; it never returns a clean ack, so consume
            # whatever comes back — possibly nothing — and move on.
            self._exchange(ser, codec.ECHO_OFF_COMMAND, require_response=False)
            # DEVICEINFO identifies the device and doubles as the presence
            # probe: an open tty proves nothing about a controller answering.
            text = self._exchange(ser, codec.DEVICE_INFO_COMMAND, require_response=False)
            if not text:
                raise DeviceNotPresentError(f"no response to DEVICEINFO at {port}")
            codec.check_response(text, codec.DEVICE_INFO_COMMAND)
            info = codec.parse_device_info(text)
            if info.module_number is None or info.serial_number is None:
                raise TransportError(f"DEVICEINFO did not identify the device: {text!r}")
            capabilities = codec.capabilities_for_module(info.module_number)
        except BaseException:
            # Never leak a half-open port; the close is best-effort.
            try:
                ser.close()
            except OSError:
                pass
            raise
        self._handle = _RS232Handle(ser)
        return TransportOpenResult(
            handle=self._handle,
            serial_number=info.serial_number,
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
        command = codec.encode_normal(channel, current_max_ma, current_set_ma)
        self._command_ack(ser, command)

    def set_active_mode(self, handle: TransportHandle, channel: int, mode: OperatingMode) -> None:
        ser = self._require_open(handle)
        self._command_ack(ser, codec.encode_mode(channel, mode))

    def close_device(self, handle: TransportHandle) -> None:
        # Idempotent by identity: only the currently open handle closes the
        # port; a stale handle is a no-op and never touches a newer session.
        if self._handle is None or handle is not self._handle:
            return
        try:
            self._handle.port.close()
        except OSError:
            # SerialException subclasses OSError; close must be no-fail — by
            # the time it runs, the server has already dropped the device_id.
            pass
        self._handle = None

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
        is pyserial's timeout face and means no response arrived.
        """
        try:
            ser.reset_input_buffer()
            ser.write(command.encode(_ENCODING) + _TX_TERMINATOR)
            ser.flush()
            data = ser.read_until(_RX_TERMINATOR)
            time.sleep(_DRAIN_DELAY_S)
            extra = ser.in_waiting
            if extra:
                data += ser.read(extra)
        except serial.SerialException as exc:
            raise TransportError(f"serial I/O failed for {command!r}: {exc}") from exc
        response = data.decode(_ENCODING, errors="replace").strip()
        if not response and require_response:
            raise TransportError(f"no response to {command!r} within {self._timeout}s")
        return response
