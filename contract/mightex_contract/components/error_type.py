"""Error-type enumeration reported in error replies."""

from __future__ import annotations

from enum import Enum


class ErrorType(str, Enum):
    """Library exception names reported in an error reply.

    These are the leaf exception types the client maps an error reply back onto.
    The abstract root MightexLEDError is intentionally absent because it is never
    raised directly. DEVICE_CONNECTION and DEVICE_NOT_FOUND are both present even
    though the latter is a subtype of the former, so the client can map directly
    to the most specific class.
    """

    # TODO (provisional): VALUE_ERROR may never appear in a server envelope,
    # because client-side Pydantic validation raises ValueError before a request
    # is ever sent. It is included for now and flagged.
    VALUE_ERROR = "ValueError"
    CONTROLLER_CLOSED = "ControllerClosedError"
    DEVICE_CONNECTION = "DeviceConnectionError"
    DEVICE_NOT_FOUND = "DeviceNotFoundError"
    DEVICE_COMMAND = "DeviceCommandError"
    UNSUPPORTED_OPERATION = "UnsupportedOperationError"
