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

from typing import Any, Protocol

from pydantic import TypeAdapter

from ..contract import Error, OpenDeviceOk, OpenDeviceReply, OpenDeviceRequest


class Backend(Protocol):
    """What link requires of a backend: run one request, return the reply dict."""

    def handle(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]: ...


_backend: Backend | None = None

_OPEN_DEVICE_REPLY: TypeAdapter[OpenDeviceOk | Error] = TypeAdapter(OpenDeviceReply)


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


def open_device(port: str | None = None) -> OpenDeviceOk:
    """Open the controller at a serial target; None means the backend default."""
    request = OpenDeviceRequest(port=port)
    reply_dict = call("open_device", request.model_dump(mode="json"))
    reply = _OPEN_DEVICE_REPLY.validate_python(reply_dict)
    if isinstance(reply, Error):
        # Placeholder until Phase 5 maps error_type to the client exception.
        raise RuntimeError(f"{reply.error_type.value}: {reply.message}")
    return reply
