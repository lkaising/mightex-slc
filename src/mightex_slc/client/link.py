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

from typing import Any, Protocol, TypeVar

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
    InitializeOk,
    InitializeReply,
    InitializeRequest,
    OpenDeviceOk,
    OpenDeviceReply,
    OpenDeviceRequest,
    OperatingMode,
    SetActiveModeOk,
    SetActiveModeReply,
    SetActiveModeRequest,
)


class Backend(Protocol):
    """What link requires of a backend: run one request, return the reply dict."""

    def handle(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]: ...


_backend: Backend | None = None

_OkT = TypeVar("_OkT", bound=ContractModel)

_OPEN_DEVICE_REPLY: TypeAdapter[OpenDeviceOk | Error] = TypeAdapter(OpenDeviceReply)
_INITIALIZE_REPLY: TypeAdapter[InitializeOk | Error] = TypeAdapter(InitializeReply)
_CONFIGURE_NORMAL_REPLY: TypeAdapter[ConfigureNormalOk | Error] = TypeAdapter(
    ConfigureNormalReply
)
_SET_ACTIVE_MODE_REPLY: TypeAdapter[SetActiveModeOk | Error] = TypeAdapter(
    SetActiveModeReply
)
_CLOSE_DEVICE_REPLY: TypeAdapter[CloseDeviceOk | Error] = TypeAdapter(CloseDeviceReply)


def use_backend(backend: Backend | None) -> None:
    """Install the backend link calls; None resets to the lazy default."""
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
    from ..transport.fake import FakeTransport

    return Server(FakeTransport())


def _roundtrip(
    operation: str,
    request: ContractModel,
    reply_adapter: TypeAdapter[_OkT | Error],
) -> _OkT:
    """Send one request across the seam and return its ok reply model."""
    reply_dict = call(operation, request.model_dump(mode="json"))
    reply = reply_adapter.validate_python(reply_dict)
    if isinstance(reply, Error):
        # Placeholder until Phase 5 maps error_type to the client exception.
        raise RuntimeError(f"{reply.error_type.value}: {reply.message}")
    return reply


def open_device(port: str | None = None) -> OpenDeviceOk:
    """Open the controller at a serial target; None means the backend default."""
    return _roundtrip("open_device", OpenDeviceRequest(port=port), _OPEN_DEVICE_REPLY)


def initialize(device_id: str) -> None:
    """Put an opened controller into host-control mode."""
    request = InitializeRequest(device_id=device_id)
    _roundtrip("initialize", request, _INITIALIZE_REPLY)


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


def set_active_mode(device_id: str, channel: int, mode: OperatingMode) -> None:
    """Switch one channel's active working mode, effective immediately."""
    request = SetActiveModeRequest(device_id=device_id, channel=channel, mode=mode)
    _roundtrip("set_active_mode", request, _SET_ACTIVE_MODE_REPLY)


def close_device(device_id: str) -> None:
    """Close an opened controller; its device_id stops being usable."""
    request = CloseDeviceRequest(device_id=device_id)
    _roundtrip("close_device", request, _CLOSE_DEVICE_REPLY)
