# ------------------------------------------------------------------------------
#  Filename: errors.py
#
#  Purpose: Client-side exception hierarchy for failed controller operations.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""Client-side exceptions raised for failed Mightex LED controller operations.

These exceptions form the library-specific error hierarchy rooted at
MightexLEDError. They are raised when an operation fails after crossing the client
API boundary, such as when the controller cannot be opened, a command is rejected,
an operation is unsupported, or a previously opened controller has been closed.

Argument validation is intentionally outside this hierarchy. Invalid user-provided
arguments should raise plain ValueError during request construction.
"""

from __future__ import annotations


class MightexLEDError(Exception):
    """Base class for all Mightex LED controller operation errors."""


class DeviceConnectionError(MightexLEDError):
    """Raised when a controller connection cannot be established or maintained."""


class DeviceNotFoundError(DeviceConnectionError):
    """Raised when no controller is found at the requested serial target."""


class DeviceCommandError(MightexLEDError):
    """Raised when the controller rejects a command.

    Attributes:
        code: The device-reported error code, when available.
    """

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class UnsupportedOperationError(MightexLEDError):
    """Raised when the requested operation is not supported by the controller."""


class ControllerClosedError(MightexLEDError):
    """Raised when an operation is attempted on a closed controller handle."""


__all__ = [
    "ControllerClosedError",
    "DeviceCommandError",
    "DeviceConnectionError",
    "DeviceNotFoundError",
    "MightexLEDError",
    "UnsupportedOperationError",
]
