# ------------------------------------------------------------------------------
#  Filename: dispatch.py
#
#  Purpose: Validates a request, routes by operation, returns a reply.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
Server-side dispatch: where an operation name plus a payload becomes a call
on the right controller.

dispatch() looks up the operation, validates the payload by constructing the
operation's Pydantic request model (which rejects unknown fields and enforces
bounds and cross-field rules), runs the matching handler against the live
device object, and returns the reply model dumped to a JSON-ready dict.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..contract import (
    CloseDeviceOk,
    CloseDeviceRequest,
    ContractModel,
    GetActiveModeOk,
    GetActiveModeRequest,
    GetNormalParametersOk,
    GetNormalParametersRequest,
    OpenDeviceOk,
    OpenDeviceRequest,
    PersistSettingsOk,
    PersistSettingsRequest,
    RestoreFactoryDefaultsOk,
    RestoreFactoryDefaultsRequest,
    SetActiveModeOk,
    SetActiveModeRequest,
    SetNormalParametersOk,
    SetNormalParametersRequest,
)
from ..transport import Transport, TransportError
from .errors import to_error, unsupported_operation
from .impl import ControllerModel
from .session import Session, UnknownDeviceError

if TYPE_CHECKING:
    from collections.abc import Callable


def dispatch(
    operation: str,
    payload: dict[str, Any],
    *,
    session: Session,
    transport: Transport,
) -> dict[str, Any]:
    """Dispatch an operation and serialize its reply."""
    route = _ROUTES.get(operation)
    if route is None:
        return unsupported_operation(operation).model_dump(mode="json")

    request_type, handler = route
    request = request_type(**payload)

    try:
        reply = handler(request, session=session, transport=transport)
    except (TransportError, UnknownDeviceError) as exc:
        reply = to_error(exc)

    return reply.model_dump(mode="json")


def _open_device(
    request: OpenDeviceRequest,
    *,
    session: Session,
    transport: Transport,
) -> OpenDeviceOk:
    """Open a controller, register it with the session, and return its identity."""
    model = ControllerModel.open(transport, port=request.port)
    device_id = session.register(model)
    return OpenDeviceOk(
        device_id=device_id,
        serial_number=model.serial_number,
        capabilities=model.capabilities,
    )


def _set_normal_parameters(
    request: SetNormalParametersRequest,
    *,
    session: Session,
    transport: Transport,
) -> SetNormalParametersOk:
    """Set the NORMAL-mode parameters of a controller channel."""
    model = session.get(request.device_id)
    model.channel(request.channel).set_normal_parameters(request.parameters)
    return SetNormalParametersOk()


def _get_normal_parameters(
    request: GetNormalParametersRequest,
    *,
    session: Session,
    transport: Transport,
) -> GetNormalParametersOk:
    """Read back the NORMAL-mode parameters of a controller channel."""
    model = session.get(request.device_id)
    parameters = model.channel(request.channel).get_normal_parameters()
    return GetNormalParametersOk(result=parameters)


def _set_active_mode(
    request: SetActiveModeRequest,
    *,
    session: Session,
    transport: Transport,
) -> SetActiveModeOk:
    """Set the active operating mode of a controller channel."""
    model = session.get(request.device_id)
    model.channel(request.channel).set_active_mode(request.mode)
    return SetActiveModeOk()


def _get_active_mode(
    request: GetActiveModeRequest,
    *,
    session: Session,
    transport: Transport,
) -> GetActiveModeOk:
    """Read back the active operating mode of a controller channel."""
    model = session.get(request.device_id)
    mode = model.channel(request.channel).get_active_mode()
    return GetActiveModeOk(result=mode)


def _persist_settings(
    request: PersistSettingsRequest,
    *,
    session: Session,
    transport: Transport,
) -> PersistSettingsOk:
    """Persist a controller's current settings to non-volatile memory."""
    model = session.get(request.device_id)
    model.persist_settings()
    return PersistSettingsOk()


def _restore_factory_defaults(
    request: RestoreFactoryDefaultsRequest,
    *,
    session: Session,
    transport: Transport,
) -> RestoreFactoryDefaultsOk:
    """Load factory defaults into a controller's current settings."""
    model = session.get(request.device_id)
    model.restore_factory_defaults()
    return RestoreFactoryDefaultsOk()


def _close_device(
    request: CloseDeviceRequest,
    *,
    session: Session,
    transport: Transport,
) -> CloseDeviceOk:
    """Remove a controller from the session and close it."""
    model = session.pop(request.device_id)
    model.close()
    return CloseDeviceOk()


_ROUTES: dict[str, tuple[type[ContractModel], Callable[..., ContractModel]]] = {
    "open_device": (OpenDeviceRequest, _open_device),
    "set_normal_parameters": (SetNormalParametersRequest, _set_normal_parameters),
    "get_normal_parameters": (GetNormalParametersRequest, _get_normal_parameters),
    "set_active_mode": (SetActiveModeRequest, _set_active_mode),
    "get_active_mode": (GetActiveModeRequest, _get_active_mode),
    "persist_settings": (PersistSettingsRequest, _persist_settings),
    "restore_factory_defaults": (RestoreFactoryDefaultsRequest, _restore_factory_defaults),
    "close_device": (CloseDeviceRequest, _close_device),
}
