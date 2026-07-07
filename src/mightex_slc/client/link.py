# ------------------------------------------------------------------------------
#  Filename: link.py
#
#  Purpose: Sends contract requests to the server and parses replies.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The client half of the contract seam, and the busiest file in this layer.

For each call it builds the operation's Pydantic request model, serializes it
with model_dump(mode="json"), calls into the server entry point, then parses the
reply against that operation's reply union. On an ok reply it returns the success
value; on an error reply it maps error_type to an exception and raises it. Every
client method ultimately goes through here.
"""

from __future__ import annotations

from typing import Any, NoReturn, Protocol, TypeVar

from pydantic import TypeAdapter

from ..contract import (
    CloseDeviceOk,
    CloseDeviceReply,
    CloseDeviceRequest,
    ConfigureNormalOk,
    ConfigureNormalReply,
    ConfigureNormalRequest,
    ContractModel,
    Error,
    ErrorType,
    OpenDeviceOk,
    OpenDeviceReply,
    OpenDeviceRequest,
    OperatingMode,
    SetActiveModeOk,
    SetActiveModeReply,
    SetActiveModeRequest,
)
from .errors import (
    ControllerClosedError,
    DeviceCommandError,
    DeviceConnectionError,
    DeviceNotFoundError,
    UnsupportedOperationError,
)


class Backend(Protocol):
    """What link requires of a backend: run one request, return the reply dict."""

    def handle(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]: ...


_backend: Backend | None = None


def use_backend(backend: Backend | None) -> None:
    """Install the backend link calls; None resets to the lazy default.

    The default backend is constructed once, on first use, and then cached;
    a changed environment takes effect only after use_backend(None).
    """
    global _backend
    _backend = backend


def call(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Send one serialized request to the backend and return the reply dict."""
    global _backend
    if _backend is None:
        _backend = _default_backend()
    return _backend.handle(operation, payload)


def _default_backend() -> Backend:
    # The one place the client reaches the server; imported lazily so the
    # client carries no server dependency until first use.
    from ..server.api import Server
    from ..transport import create_transport

    return Server(create_transport())


_OkT = TypeVar("_OkT", bound=ContractModel)

# VALUE_ERROR is defensive: validation raises ValueError client-side before a
# request is sent, so the server never emits it today.
_ERROR_EXCEPTIONS: dict[ErrorType, type[Exception]] = {
    ErrorType.VALUE_ERROR: ValueError,
    ErrorType.CONTROLLER_CLOSED: ControllerClosedError,
    ErrorType.DEVICE_CONNECTION: DeviceConnectionError,
    ErrorType.DEVICE_NOT_FOUND: DeviceNotFoundError,
    ErrorType.UNSUPPORTED_OPERATION: UnsupportedOperationError,
}


def _raise_error(reply: Error) -> NoReturn:
    """Raise the client exception matching one error reply."""
    if reply.error_type is ErrorType.DEVICE_COMMAND:
        raise DeviceCommandError(reply.message, code=reply.code)
    raise _ERROR_EXCEPTIONS[reply.error_type](reply.message)


def _roundtrip(
    operation: str,
    request: ContractModel,
    reply_adapter: TypeAdapter[_OkT | Error],
) -> _OkT:
    """Send one request across the seam and return its ok reply model."""
    reply_dict = call(operation, request.model_dump(mode="json"))
    reply = reply_adapter.validate_python(reply_dict)
    if isinstance(reply, Error):
        _raise_error(reply)
    return reply


_OPEN_DEVICE_REPLY: TypeAdapter[OpenDeviceOk | Error] = TypeAdapter(
    OpenDeviceReply
)
_CONFIGURE_NORMAL_REPLY: TypeAdapter[ConfigureNormalOk | Error] = TypeAdapter(
    ConfigureNormalReply
)
_SET_ACTIVE_MODE_REPLY: TypeAdapter[SetActiveModeOk | Error] = TypeAdapter(
    SetActiveModeReply
)
_CLOSE_DEVICE_REPLY: TypeAdapter[CloseDeviceOk | Error] = TypeAdapter(
    CloseDeviceReply
)


def open_device(
    port: str | None = None
) -> OpenDeviceOk:
    """Open the controller at a serial target; None means the backend default."""
    request = OpenDeviceRequest(
        port=port
    )
    return _roundtrip("open_device", request, _OPEN_DEVICE_REPLY)


def configure_normal(
    device_id: str,
    channel: int,
    current_max_ma: float,
    current_set_ma: float,
) -> None:
    """Store NORMAL-mode current parameters for one channel; output unchanged."""
    request = ConfigureNormalRequest(
        device_id=device_id,
        channel=channel,
        current_max_ma=current_max_ma,
        current_set_ma=current_set_ma,
    )
    _roundtrip("configure_normal", request, _CONFIGURE_NORMAL_REPLY)


def set_active_mode(
    device_id: str,
    channel: int,
    mode: OperatingMode
) -> None:
    """Switch one channel's active working mode, effective immediately."""
    request = SetActiveModeRequest(
        device_id=device_id,
        channel=channel,
        mode=mode
    )
    _roundtrip("set_active_mode", request, _SET_ACTIVE_MODE_REPLY)


def close_device(
    device_id: str
) -> None:
    """Close an opened controller; its device_id stops being usable."""
    request = CloseDeviceRequest(
        device_id=device_id
    )
    _roundtrip("close_device", request, _CLOSE_DEVICE_REPLY)
