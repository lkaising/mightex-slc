# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The transport package: swappable backends behind one interface.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The transport package: the swappable bottom layer of the stack.

It exposes one interface that the server device model drives, with two
implementations behind it: a pure-Python fake and the real serial path. Both
are constructed explicitly by name — FakeTransport() or RS232Transport() —
never by ambient configuration, so which device is behind the server is always
a value in scope at the call site. The backend re-exports are lazy so naming
one backend never imports the other (and never imports pyserial).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import (
    CommandRejectedError,
    DeviceNotPresentError,
    InvalidHandleError,
    Transport,
    TransportError,
    TransportHandle,
    TransportOpenResult,
)

if TYPE_CHECKING:
    from .fake import FakeTransport
    from .rs232 import RS232Transport

__all__ = [
    "CommandRejectedError",
    "DeviceNotPresentError",
    "FakeTransport",
    "InvalidHandleError",
    "RS232Transport",
    "Transport",
    "TransportError",
    "TransportHandle",
    "TransportOpenResult",
]


def __getattr__(name: str):
    # Lazy re-exports (PEP 562): naming one backend must never import the
    # other, and RS232Transport drags in pyserial.
    if name == "FakeTransport":
        from .fake import FakeTransport

        return FakeTransport
    if name == "RS232Transport":
        from .rs232 import RS232Transport

        return RS232Transport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
