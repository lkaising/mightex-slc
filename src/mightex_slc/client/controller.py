# ------------------------------------------------------------------------------
#  Filename: controller.py
#
#  Purpose: Client-side proxy for one open controller, identified by device_id.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The Controller proxy: the client-side stand-in for a device that lives on the
server.

open_device lives here too: it is the library's entry point, crossing the seam
once and wrapping the reply in a Controller. A Controller holds the device_id
returned at open plus the capabilities reported alongside it, cached so
questions like requires_initialization answer without a round trip. Its methods
each build the matching device-level contract request and send it through link;
this slice carries initialize and close, and later slices add the rest.
channel(n) is a pure client-side accessor: it builds a Channel proxy without
crossing the seam. Context-manager support (with open_device(...) as ctrl) is
wired here, so the controller closes itself on exit.
"""

from __future__ import annotations

from types import TracebackType

from . import link
from .channel import Channel
from .types import ControllerCapabilities


def open_device(port: str | None = None) -> Controller:
    """Open the controller at a serial target; None means the backend default."""
    reply = link.open_device(port=port)
    return Controller(device_id=reply.device_id, capabilities=reply.capabilities)


class Controller:
    """One open controller, addressed by the device_id returned at open."""

    def __init__(self, device_id: str, capabilities: ControllerCapabilities) -> None:
        self._device_id = device_id
        self._capabilities = capabilities
        self._closed = False

    @property
    def requires_initialization(self) -> bool:
        """Whether initialize() must run before channel-control operations."""
        return self._capabilities.requires_initialization

    @property
    def is_closed(self) -> bool:
        """Whether close() has completed on this controller."""
        return self._closed

    def initialize(self) -> None:
        """Put the controller into host-control mode."""
        link.initialize(self._device_id)

    def channel(self, number: int) -> Channel:
        """Return a proxy for one one-based channel; never crosses the seam."""
        return Channel(self._device_id, number)

    def close(self) -> None:
        """Close the controller; after the first success, later calls are no-ops."""
        if self._closed:
            return
        link.close_device(self._device_id)
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
