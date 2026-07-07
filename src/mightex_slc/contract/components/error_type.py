# ------------------------------------------------------------------------------
#  Filename: error_type.py
#
#  Purpose: Define error type names used in operation error replies.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from enum import StrEnum


class ErrorType(StrEnum):
    """Concrete error types returned in operation failure replies.

    Values mirror the client exception classes used to reconstruct failures
    across the transport boundary.
    """

    DEVICE_CONNECTION = "DeviceConnectionError"
    DEVICE_NOT_FOUND = "DeviceNotFoundError"
    DEVICE_COMMAND = "DeviceCommandError"
    UNSUPPORTED_OPERATION = "UnsupportedOperationError"
    CONTROLLER_CLOSED = "ControllerClosedError"
