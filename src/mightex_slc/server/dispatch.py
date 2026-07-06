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

from ..contract import ContractModel, OpenDeviceOk, OpenDeviceRequest
from ..transport import Transport
from .session import Session


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
        # Placeholder until the error envelope arrives with the Phase 4 fan-out.
        raise ValueError(f"unknown operation: {operation!r}") from None
    request = request_type(**payload)
    reply = handler(request, session=session, transport=transport)
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


_ROUTES: dict[str, tuple[type[ContractModel], Callable[..., ContractModel]]] = {
    "open_device": (OpenDeviceRequest, _open_device),
}
