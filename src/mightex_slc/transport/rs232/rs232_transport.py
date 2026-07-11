# ------------------------------------------------------------------------------
#  Filename: rs232_transport.py
#
#  Purpose: Real serial backend: the Transport implementation over pyserial.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""Implement the serial Transport backend over pyserial.

The caller must provide an explicit port. Each transport instance owns at most
one physical port, using exclusive access where supported, and identifies the
controller before returning an open handle.
"""

from __future__ import annotations

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
from . import codec, serial_link
from .capabilities import capabilities_for_module

if TYPE_CHECKING:
    from collections.abc import Callable

    from ...contract import ControllerCapabilities, OperatingMode


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
        baudrate: int = serial_link.DEFAULT_BAUDRATE,
        timeout: float = serial_link.DEFAULT_TIMEOUT_S,
        serial_factory: Callable[..., serial.Serial] = serial.Serial,
    ) -> None:
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial_factory = serial_factory
        self._handle: _RS232Handle | None = None

    def open_device(self, port: str | None = None) -> TransportOpenResult:
        """Open the RS232 controller on a serial port and return its transport handle."""
        if self._handle is not None:
            raise TransportError("device is already open")
        if port is None:
            raise TransportError("no serial port specified")

        serial_port = serial_link.open_serial_port(
            port,
            baudrate=self._baudrate,
            timeout=self._timeout,
            serial_factory=self._serial_factory,
        )

        try:
            serial_number, capabilities = self._identify_controller(serial_port, port)
        except BaseException:
            serial_link.close_quietly(serial_port)
            raise

        handle = _RS232Handle(serial_port)
        self._handle = handle

        return TransportOpenResult(
            handle=handle,
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
        """Send the normal-mode current limits for one channel."""
        serial_port = self._require_open(handle)
        self._command_ack(
            serial_port,
            codec.encode_normal(channel, current_max_ma, current_set_ma),
        )

    def set_active_mode(
        self,
        handle: TransportHandle,
        channel: int,
        mode: OperatingMode,
    ) -> None:
        """Send the operating-mode command for one channel."""
        serial_port = self._require_open(handle)
        self._command_ack(serial_port, codec.encode_mode(channel, mode))

    def close_device(self, handle: TransportHandle) -> None:
        """Close the current handle, ignoring stale or already-closed handles."""
        if self._handle is None or handle is not self._handle:
            return

        # The server has already dropped the device_id; close must not fail.
        serial_link.close_quietly(self._handle.port)
        self._handle = None

    def _identify_controller(
        self,
        serial_port: serial.Serial,
        port: str,
    ) -> tuple[str, ControllerCapabilities]:
        """Confirm a controller is answering and read its identity.

        ECHOOFF enters PC Mode on MA/CA modules (hygiene elsewhere) and
        never returns a clean ack, so its reply, possibly nothing, is
        consumed and ignored. DEVICEINFO then doubles as the presence
        probe, because an open tty proves nothing about a controller
        answering: silence maps to DeviceNotPresentError rather than
        serial_link.exchange's TransportError. Returns (serial_number,
        capabilities).
        """
        serial_link.exchange(
            serial_port,
            codec.ECHO_OFF_COMMAND,
            require_response=False,
        )
        response = serial_link.exchange(
            serial_port,
            codec.DEVICE_INFO_COMMAND,
            require_response=False,
        )
        if not response:
            raise DeviceNotPresentError(f"no response to DEVICEINFO at {port}")

        codec.check_response(response, codec.DEVICE_INFO_COMMAND)
        info = codec.parse_device_info(response)
        if info.module_number is None or info.serial_number is None:
            raise TransportError(f"DEVICEINFO did not identify the device: {response!r}")

        capabilities = capabilities_for_module(info.module_number)
        return info.serial_number, capabilities

    def _require_open(self, handle: TransportHandle) -> serial.Serial:
        if self._handle is None or handle is not self._handle:
            raise InvalidHandleError("handle is not open")
        return self._handle.port

    def _command_ack(self, serial_port: serial.Serial, command: str) -> None:
        response = serial_link.exchange(serial_port, command)
        codec.require_ack(response, command)
