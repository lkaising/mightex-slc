# ------------------------------------------------------------------------------
#  Filename: base.py
#
#  Purpose: The transport interface both backends satisfy; the swap seam.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The interface both backends satisfy: the swap seam.

It defines the hardware-agnostic transport contract the server device model
drives: open the controller at a serial-port target, issue the slice's
per-device and per-channel operations against an opaque handle, and close that
handle. Because the device model only knows this interface, the fake and the
real backend are interchangeable, and nothing above transport knows or cares
which is in use.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..contract import ControllerCapabilities, OperatingMode


class TransportError(Exception):
    """Root of transport-level failures.

    Raised directly when no subtype fits, for example opening a device that
    is already held open.
    """


class DeviceNotPresentError(TransportError):
    """Nothing answers at the requested serial port."""


class InvalidHandleError(TransportError):
    """An operation used a handle that is not currently open."""


class CommandRejectedError(TransportError):
    """The device refused a command.

    The transport-level face of the device's #? / #! responses, for example a
    channel number or a current outside the device's range.
    """


class TransportHandle:
    """Opaque token identifying one open device at the transport level.

    This is not the public device_id; the server session owns that mapping.
    Handles compare by identity, and a backend may subclass to attach its own
    payload (the rs232 backend will hold the serial port).
    """


@dataclass(frozen=True, slots=True)
class TransportOpenResult:
    """Everything opening a device yields: the live handle, the device's
    serial number, and its capabilities."""

    handle: TransportHandle
    serial_number: str
    capabilities: ControllerCapabilities


class Transport(ABC):
    """The interface the server drives; carries the slice's four operations.

    It is allowed to grow with later slices without the contract moving.
    close_device is idempotent and never a safety action; every other
    handle-taking operation raises InvalidHandleError on a handle that is
    not currently open.
    """

    @abstractmethod
    def open_device(self, port: str | None = None) -> TransportOpenResult:
        """Open the controller at a serial-port target and return its handle,
        serial number, and capabilities. port is the serial device path
        (e.g. /dev/cu.usbserial-A6002xyz); each transport decides what None
        means — the fake accepts and ignores it (it is the device at whatever
        target the caller imagines), the rs232 backend refuses the open. A
        transport never scans or probes ports — it opens only the one it is told to
        (opening is side-effecting: the backend enters host control by sending
        ECHOOFF, which is PC-Mode entry on MA/CA modules). Raises
        DeviceNotPresentError when nothing answers at the port, TransportError
        when the device is already held open."""

    @abstractmethod
    def configure_normal(
        self,
        handle: TransportHandle,
        channel: int,
        current_max_ma: float,
        current_set_ma: float,
    ) -> None:
        """Store NORMAL-mode parameters for a one-based channel. Storing
        never changes output; raises CommandRejectedError when the device
        refuses the arguments."""

    @abstractmethod
    def set_active_mode(self, handle: TransportHandle, channel: int, mode: OperatingMode) -> None:
        """Make a mode active on a one-based channel, effective immediately.
        This is the only operation that changes output; raises
        CommandRejectedError when the device refuses the channel or mode."""

    @abstractmethod
    def close_device(self, handle: TransportHandle) -> None:
        """Release an open handle. Idempotent: closing a stale handle is a
        no-op and never touches a newer session. Closing is not a safety
        action — the device keeps driving its outputs afterwards."""
