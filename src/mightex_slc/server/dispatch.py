# ------------------------------------------------------------------------------
#  Filename: dispatch.py
#
#  Purpose: Validates a request, routes by operation, returns a reply.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The router and the server-side validation point.

It validates an incoming request by constructing the matching Pydantic request
model, which rejects unknown fields and enforces the bounds and cross-field
rules. It then routes by operation name to the right handler on the live device
object, takes the result, and wraps it in the operation's reply model. This is
where an operation name plus a payload becomes a call on the right controller.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..contract import (
    CloseDeviceOk,
    CloseDeviceRequest,
    ConfigureNormalOk,
    ConfigureNormalRequest,
    ContractModel,
    InitializeOk,
    InitializeRequest,
    OpenDeviceOk,
    OpenDeviceRequest,
    SetActiveModeOk,
    SetActiveModeRequest,
)
from ..transport import Transport, TransportError
from .errors import to_error, unsupported_operation
from .session import Session, UnknownDeviceError


def dispatch(
    operation: str,
    payload: dict[str, Any],
    *,
    session: Session,
    transport: Transport,
) -> dict[str, Any]:
    """Validate a payload, route it to its handler, and return the reply dict."""
    try:
        request_type, handler = _ROUTES[operation]
    except KeyError:
        return unsupported_operation(operation).model_dump(mode="json")
    request = request_type(**payload)
    try:
        reply = handler(request, session=session, transport=transport)
    except (TransportError, UnknownDeviceError) as exc:
        # Known operational failures cross the seam as data; anything else is
        # a bug and keeps raising. Validation errors from the request rebuild
        # above also stay raw for now — inert with the in-process client.
        reply = to_error(exc)
    return reply.model_dump(mode="json")


def _open_device(
    request: OpenDeviceRequest,
    *,
    session: Session,
    transport: Transport,
) -> OpenDeviceOk:
    result = transport.open_device(port=request.port)
    device_id = session.register(result.handle)
    return OpenDeviceOk(
        device_id=device_id,
        serial_number=result.serial_number,
        capabilities=result.capabilities,
    )


def _initialize(
    request: InitializeRequest,
    *,
    session: Session,
    transport: Transport,
) -> InitializeOk:
    handle = session.get(request.device_id)
    transport.initialize(handle)
    return InitializeOk()


def _configure_normal(
    request: ConfigureNormalRequest,
    *,
    session: Session,
    transport: Transport,
) -> ConfigureNormalOk:
    handle = session.get(request.device_id)
    transport.configure_normal(
        handle, request.channel, request.current_max_ma, request.current_set_ma
    )
    return ConfigureNormalOk()


def _set_active_mode(
    request: SetActiveModeRequest,
    *,
    session: Session,
    transport: Transport,
) -> SetActiveModeOk:
    handle = session.get(request.device_id)
    transport.set_active_mode(handle, request.channel, request.mode)
    return SetActiveModeOk()


def _close_device(
    request: CloseDeviceRequest,
    *,
    session: Session,
    transport: Transport,
) -> CloseDeviceOk:
    # Pop before the transport close: the device_id must stop resolving even
    # though transport close is idempotent and documented no-fail.
    handle = session.pop(request.device_id)
    transport.close_device(handle)
    return CloseDeviceOk()


_ROUTES: dict[str, tuple[type[ContractModel], Callable[..., ContractModel]]] = {
    "open_device": (OpenDeviceRequest, _open_device),
    "initialize": (InitializeRequest, _initialize),
    "configure_normal": (ConfigureNormalRequest, _configure_normal),
    "set_active_mode": (SetActiveModeRequest, _set_active_mode),
    "close_device": (CloseDeviceRequest, _close_device),
}
