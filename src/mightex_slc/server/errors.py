# ------------------------------------------------------------------------------
#  Filename: errors.py
#
#  Purpose: Maps raised exceptions to the contract Error envelope.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The exception-to-envelope mapper, counterpart to the client's errors module.

When the device model or validation raises, this turns that exception into an
Error reply: it sets the status, the error_type from the exception class, the
message, and the code when the device reported one. Together with the client's
error module, it lets an exception raised deep in the server surface as the same
exception type on the client.
"""

from __future__ import annotations

from ..contract import Error, ErrorType
from ..transport import (
    CommandRejectedError,
    DeviceNotPresentError,
    InvalidHandleError,
    TransportError,
)
from .session import UnknownDeviceError


def unsupported_operation(operation: str) -> Error:
    """Envelope for an operation name dispatch has no route for."""
    return Error(
        error_type=ErrorType.UNSUPPORTED_OPERATION,
        message=f"unknown operation: {operation!r}",
    )


def to_error(exc: UnknownDeviceError | TransportError) -> Error:
    """Convert a known operational failure into its Error envelope.

    Only session and transport failures belong here; anything else is a bug
    and must keep raising instead of crossing the seam as data. No device
    code is ever attached: the vendor's post-#! Error command is undocumented
    (device_and_protocol.md §4), so nothing reports one yet.
    """
    return Error(error_type=_classify(exc), message=str(exc))


def _classify(exc: UnknownDeviceError | TransportError) -> ErrorType:
    # Transport subtypes must be checked before their TransportError root.
    if isinstance(exc, UnknownDeviceError):
        return ErrorType.CONTROLLER_CLOSED
    if isinstance(exc, InvalidHandleError):
        # A stale transport handle is a closed controller from the client's
        # view; defense in depth behind the session's own device_id check.
        return ErrorType.CONTROLLER_CLOSED
    if isinstance(exc, DeviceNotPresentError):
        return ErrorType.DEVICE_NOT_FOUND
    if isinstance(exc, CommandRejectedError):
        return ErrorType.DEVICE_COMMAND
    return ErrorType.DEVICE_CONNECTION
