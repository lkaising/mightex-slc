# ------------------------------------------------------------------------------
#  Filename: link.py
#
#  Purpose: Sends contract requests to a request executor and parses replies.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The client half of the contract seam, and the busiest file in this layer.

Every function here is stateless plumbing over a caller-supplied
RequestExecutor: build the operation's Pydantic request model, serialize it
with model_dump(mode="json"), hand it to the executor, then parse the reply
against that operation's reply union. On an ok reply it returns the success
value; on an error reply it maps error_type to an exception and raises it.
Every client method ultimately goes through here. The module holds no state of
any kind: which executor runs a request is decided by the Controller it was
pinned to at open, never by anything ambient.
"""

from __future__ import annotations

from typing import Any, NoReturn, Protocol

from pydantic import TypeAdapter

from ..contract import (
    CloseDeviceOk,
    CloseDeviceReply,
    CloseDeviceRequest,
    ContractModel,
    Error,
    ErrorType,
    GetActiveModeOk,
    GetActiveModeReply,
    GetActiveModeRequest,
    GetNormalParametersOk,
    GetNormalParametersReply,
    GetNormalParametersRequest,
    NormalParameters,
    OpenDeviceOk,
    OpenDeviceReply,
    OpenDeviceRequest,
    OperatingMode,
    SetActiveModeOk,
    SetActiveModeReply,
    SetActiveModeRequest,
    SetNormalParametersOk,
    SetNormalParametersReply,
    SetNormalParametersRequest,
)
from .errors import (
    ControllerClosedError,
    DeviceCommandError,
    DeviceConnectionError,
    DeviceNotFoundError,
    UnsupportedOperationError,
)


class RequestExecutor(Protocol):
    """Runs one serialized contract request and returns its reply dict."""

    def handle(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]: ...


_ERROR_EXCEPTIONS: dict[ErrorType, type[Exception]] = {
    ErrorType.DEVICE_CONNECTION: DeviceConnectionError,
    ErrorType.DEVICE_NOT_FOUND: DeviceNotFoundError,
    ErrorType.UNSUPPORTED_OPERATION: UnsupportedOperationError,
    ErrorType.CONTROLLER_CLOSED: ControllerClosedError,
}


def _raise_error(reply: Error) -> NoReturn:
    """Raise the client exception matching one error reply."""
    if reply.error_type is ErrorType.DEVICE_COMMAND:
        raise DeviceCommandError(reply.message, code=reply.code)
    raise _ERROR_EXCEPTIONS[reply.error_type](reply.message)


def _roundtrip[OkT: ContractModel](
    executor: RequestExecutor,
    operation: str,
    request: ContractModel,
    reply_adapter: TypeAdapter[OkT | Error],
) -> OkT:
    """Send one request across the seam and return its ok reply model."""
    reply_dict = executor.handle(operation, request.model_dump(mode="json"))
    reply = reply_adapter.validate_python(reply_dict)
    if isinstance(reply, Error):
        _raise_error(reply)
    return reply


_OPEN_DEVICE_REPLY: TypeAdapter[OpenDeviceOk | Error] = TypeAdapter(OpenDeviceReply)
_SET_NORMAL_PARAMETERS_REPLY: TypeAdapter[SetNormalParametersOk | Error] = TypeAdapter(
    SetNormalParametersReply
)
_GET_NORMAL_PARAMETERS_REPLY: TypeAdapter[GetNormalParametersOk | Error] = TypeAdapter(
    GetNormalParametersReply
)
_SET_ACTIVE_MODE_REPLY: TypeAdapter[SetActiveModeOk | Error] = TypeAdapter(SetActiveModeReply)
_GET_ACTIVE_MODE_REPLY: TypeAdapter[GetActiveModeOk | Error] = TypeAdapter(GetActiveModeReply)
_CLOSE_DEVICE_REPLY: TypeAdapter[CloseDeviceOk | Error] = TypeAdapter(CloseDeviceReply)


def open_device(executor: RequestExecutor, port: str | None = None) -> OpenDeviceOk:
    """Open the controller at a serial target; the transport decides what None means."""
    request = OpenDeviceRequest(port=port)
    return _roundtrip(executor, "open_device", request, _OPEN_DEVICE_REPLY)


def set_normal_parameters(
    executor: RequestExecutor,
    device_id: str,
    channel: int,
    parameters: NormalParameters,
) -> None:
    """Store NORMAL-mode current parameters for one channel; output unchanged."""
    request = SetNormalParametersRequest(
        device_id=device_id, channel=channel, parameters=parameters
    )
    _roundtrip(executor, "set_normal_parameters", request, _SET_NORMAL_PARAMETERS_REPLY)


def get_normal_parameters(
    executor: RequestExecutor,
    device_id: str,
    channel: int,
) -> NormalParameters:
    """Read back the NORMAL-mode parameters stored for one channel."""
    request = GetNormalParametersRequest(device_id=device_id, channel=channel)
    return _roundtrip(
        executor, "get_normal_parameters", request, _GET_NORMAL_PARAMETERS_REPLY
    ).result


def set_active_mode(
    executor: RequestExecutor,
    device_id: str,
    channel: int,
    mode: OperatingMode,
) -> None:
    """Switch one channel's active working mode, effective immediately."""
    request = SetActiveModeRequest(device_id=device_id, channel=channel, mode=mode)
    _roundtrip(executor, "set_active_mode", request, _SET_ACTIVE_MODE_REPLY)


def get_active_mode(
    executor: RequestExecutor,
    device_id: str,
    channel: int,
) -> OperatingMode:
    """Read back the mode currently driving one channel."""
    request = GetActiveModeRequest(device_id=device_id, channel=channel)
    return _roundtrip(executor, "get_active_mode", request, _GET_ACTIVE_MODE_REPLY).result


def close_device(executor: RequestExecutor, device_id: str) -> None:
    """Close an opened controller; its device_id stops being usable."""
    request = CloseDeviceRequest(device_id=device_id)
    _roundtrip(executor, "close_device", request, _CLOSE_DEVICE_REPLY)
