# ------------------------------------------------------------------------------
#  Filename: session.py
#
#  Purpose: Owns the live Controller objects, keyed by device_id.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The registry that owns the live Controller objects, keyed by device_id.

This is where actual device state lives, the state the client only ever
references by id. Opening a device creates a controller here and hands back its
id; closing one disposes it; every other operation looks up its controller here
first. It is the lifecycle and ownership manager for open devices.
"""

from __future__ import annotations

from uuid import uuid4

from .impl import ControllerModel


class UnknownDeviceError(Exception):
    """An operation referenced a device_id the session does not hold.

    Raised both for ids that were never registered and for ids already
    removed by close; either way the controller is not usable, so the server
    maps this to a controller-closed error reply.
    """


class Session:
    """Registry of open devices, mapping public device_id to live model.

    The public device_id is generated here, at registration time; the
    controller model (and the transport handle inside it) never leaves the
    server.
    """

    def __init__(self) -> None:
        self._models: dict[str, ControllerModel] = {}

    def register(self, model: ControllerModel) -> str:
        """Register a newly opened controller and return its new device_id."""
        device_id = uuid4().hex
        self._models[device_id] = model
        return device_id

    def get(self, device_id: str) -> ControllerModel:
        """Return the live controller model for a device_id."""
        try:
            return self._models[device_id]
        except KeyError:
            raise UnknownDeviceError(f"unknown or closed device_id: {device_id!r}") from None

    def pop(self, device_id: str) -> ControllerModel:
        """Remove and return the live controller model for a device_id."""
        try:
            return self._models.pop(device_id)
        except KeyError:
            raise UnknownDeviceError(f"unknown or closed device_id: {device_id!r}") from None
