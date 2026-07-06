# ------------------------------------------------------------------------------
#  Filename: error_type.py
#
#  Purpose: Define error type names used in operation error replies.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class ErrorType(str, Enum):
    """Concrete error types returned in operation failure replies.

    Values mirror the client exception classes used to reconstruct failures
    across the transport boundary.
    """

    # TODO: VALUE_ERROR may never appear in a server envelope, because
    # client-side Pydantic validation raises ValueError before a request is
    # sent. Deliberately deferred until server/client error behavior exists
    # (post-Phase 1).
    VALUE_ERROR = "ValueError"
    CONTROLLER_CLOSED = "ControllerClosedError"
    DEVICE_CONNECTION = "DeviceConnectionError"
    DEVICE_NOT_FOUND = "DeviceNotFoundError"
    DEVICE_COMMAND = "DeviceCommandError"
    UNSUPPORTED_OPERATION = "UnsupportedOperationError"
