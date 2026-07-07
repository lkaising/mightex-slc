# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The rs232 backend package; the private wire format lives here.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The rs232 backend package: the real serial path.

This is the only place the device wire protocol lives. The codec module owns the
encode and decode of the RS232 command format, and the transport module drives it
over pyserial. Nothing above transport sees these bytes.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rs232_transport import RS232Transport

__all__ = [
    "RS232Transport",
]


def __getattr__(name: str):
    # Lazy re-export (PEP 562): the transport drags in pyserial, and loading
    # it eagerly here would break the codec's promise of being importable
    # and testable with no serial dependency.
    if name == "RS232Transport":
        from .rs232_transport import RS232Transport

        return RS232Transport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
