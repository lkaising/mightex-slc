# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The transport package: swappable backends behind one interface.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The transport package: the swappable bottom layer of the stack.

It exposes one interface that the device model drives, with two implementations
behind it: a pure-Python fake and the real serial path. This is what lets the
whole stack be built and run with no hardware, then pointed at a real
controller by changing one line. Beyond marking the package, this module
carries the small factory that returns the chosen backend, so the server asks
for a transport without hard-coding which one.
"""

from __future__ import annotations

import os

from .base import (
    CommandRejectedError,
    DeviceNotPresentError,
    InvalidHandleError,
    Transport,
    TransportError,
    TransportHandle,
    TransportOpenResult,
)

def create_transport(backend: str | None = None) -> Transport:
    """Return the chosen transport backend.

    Selection order: the backend argument, else the MIGHTEX_SLC_BACKEND
    environment variable, else "rs232". The rs232 backend reads its default
    serial port from MIGHTEX_SLC_PORT (unset means open_device must be given
    an explicit port); "fake" is the in-memory simulated controller. Imports
    are lazy so selecting one backend never imports the other.
    """
    name = backend or os.environ.get("MIGHTEX_SLC_BACKEND") or "rs232"
    name = name.strip().lower()
    if name == "rs232":
        from .rs232 import RS232Transport

        return RS232Transport(default_port=os.environ.get("MIGHTEX_SLC_PORT"))
    if name == "fake":
        from .fake import FakeTransport

        return FakeTransport()
    raise ValueError(f"unknown transport backend: {name!r}")


__all__ = [
    "CommandRejectedError",
    "DeviceNotPresentError",
    "InvalidHandleError",
    "Transport",
    "TransportError",
    "TransportHandle",
    "TransportOpenResult",
    "create_transport",
]
