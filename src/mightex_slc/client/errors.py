# ------------------------------------------------------------------------------
#  Filename: errors.py
#
#  Purpose: Exception hierarchy the client raises from error replies.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The exception hierarchy the client raises, rooted at MightexLEDError.

The tree covers connection, not-found, command, unsupported-operation, and
controller-closed errors. These are raised on the client side: when a reply comes
back as an error envelope, link reads its error_type and raises the matching class
from here. It is the human-facing error vocabulary, the counterpart to the
server's exception-to-envelope mapping. Argument validation is not part of this
tree: bad arguments raise plain ValueError at request construction.
"""

from __future__ import annotations


class MightexLEDError(Exception):
    """Root of every error the library raises for a failed operation."""


class DeviceConnectionError(MightexLEDError):
    """The connection to the controller failed or could not be established."""


class DeviceNotFoundError(DeviceConnectionError):
    """No controller was present at the requested serial target."""


class DeviceCommandError(MightexLEDError):
    """The controller rejected a command.

    Carries the device's error code when the controller reports one; code is
    None otherwise.
    """

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class UnsupportedOperationError(MightexLEDError):
    """The requested operation is not supported."""


class ControllerClosedError(MightexLEDError):
    """The controller behind this device_id is no longer open."""


__all__ = [
    "ControllerClosedError",
    "DeviceCommandError",
    "DeviceConnectionError",
    "DeviceNotFoundError",
    "MightexLEDError",
    "UnsupportedOperationError",
]
