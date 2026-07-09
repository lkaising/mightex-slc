# ------------------------------------------------------------------------------
#  Filename: api.py
#
#  Purpose: Server entry point that client link calls into.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The server's front door: the entry point client/link.py calls into.

It receives a serialized request (operation name plus data) and hands it to
dispatch. Server is the in-process implementation of the client's
RequestExecutor protocol: the client constructs one per open and pins it to
the Controller it returns. In the current single-process design this is a
direct in-process call rather than a network endpoint, but keeping it as an
explicit boundary is deliberate: if a local socket or daemon is ever added,
it slots in here as another RequestExecutor without the contract or the rest
of the stack moving.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .dispatch import dispatch
from .session import Session

if TYPE_CHECKING:
    from ..transport import Transport


class Server:
    """The in-process server: one transport binding and one session registry."""

    __slots__ = ("_session", "_transport")

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._session = Session()

    def handle(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Run one serialized request and return its JSON-mode reply dict."""
        return dispatch(operation, payload, session=self._session, transport=self._transport)

    def __repr__(self) -> str:
        transport = type(self._transport).__name__
        return f"<{type(self).__name__} transport={transport} {self._session!r}>"
