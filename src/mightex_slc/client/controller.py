# ------------------------------------------------------------------------------
#  Filename: controller.py
#
#  Purpose: Client-side proxy for one open controller; open_device lives here.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The Controller proxy: the client-side stand-in for a device that lives on the
server.

open_device lives here too as the library's entry point. It resolves the
request executor exactly once — wrapping the given (or freshly constructed)
transport in an in-process Server — crosses the seam, and pins that executor
to the Controller it returns, so the device_id and the only thing that can
resolve it always travel together. open_fake_device is the explicit
no-hardware spelling; the fake is never reachable by omission.

A Controller holds the executor, the device_id returned at open, and the
capabilities reported alongside it, cached so capability questions answer
without a round trip. channel(n) is a pure client-side accessor: it builds a
Channel proxy carrying the same executor without crossing the seam.
Context-manager support (with open_device(...) as ctrl) is wired here, so the
controller closes itself on exit.
"""

from __future__ import annotations

from types import TracebackType

from ..transport import Transport
from . import link
from .channel import Channel
from .types import ControllerCapabilities


def open_device(port: str | None = None, *, transport: Transport | None = None) -> Controller:
    """Open a controller and return a proxy for it.

    Args:
        port: Serial port path of the controller, such as "/dev/ttyUSB0".
        transport: Optional transport implementation for tests or custom
            integrations; port is forwarded to it. Use open_fake_device()
            for the built-in simulated controller.

    Returns:
        A Controller for the opened device.

    Raises:
        ValueError: If neither port nor transport is given.
        DeviceNotFoundError: If nothing responds at the requested port.
        DeviceConnectionError: If the transport cannot be opened or the
            connection fails for another reason.
    """
    if port is None and transport is None:
        raise ValueError(
            "no serial port specified: pass one, e.g. open_device('/dev/ttyUSB0'), "
            "or use open_fake_device() for the in-memory simulated controller"
        )
    # Local imports: neither pyserial nor the server package loads until a device is opened.
    if transport is None:
        from ..transport.rs232 import RS232Transport

        transport = RS232Transport()
    from ..server.api import Server

    executor = Server(transport)
    reply = link.open_device(executor, port=port)
    return Controller(executor, reply.device_id, reply.capabilities)


def open_fake_device() -> Controller:
    """Open the built-in simulated controller; no hardware is required.

    Returns:
        A Controller for the simulated device.
    """
    from ..transport.fake import FakeTransport

    return open_device(transport=FakeTransport())


class Controller:
    """One open controller: the executor it was opened on plus its device_id.

    The pairing is the point: a device_id is only meaningful to the executor
    whose session minted it, so they travel together and every later call —
    including close — deterministically reaches the same server.
    """

    def __init__(
        self,
        executor: link.RequestExecutor,
        device_id: str,
        capabilities: ControllerCapabilities,
    ) -> None:
        self._executor = executor
        self._device_id = device_id
        self._capabilities = capabilities
        self._closed = False

    @property
    def is_closed(self) -> bool:
        """Whether close() has completed on this controller."""
        return self._closed

    def channel(self, number: int) -> Channel:
        """Return a proxy for the given channel (1-based); never crosses the seam."""
        return Channel(self._executor, self._device_id, number)

    def close(self) -> None:
        """Close the controller; after the first success, later calls are no-ops."""
        if self._closed:
            return
        link.close_device(self._executor, self._device_id)
        self._closed = True

    def __enter__(self) -> Controller:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
