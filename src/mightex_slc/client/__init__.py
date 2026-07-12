# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: Public surface of the library; the entry points users import.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The public surface of the library: what a user imports.

This module exposes the top-level entry points (open_device and
open_fake_device) and re-exports the enums, types, and exception classes users
are meant to reach. If a name is not surfaced here, it is not part of the
public API. It mirrors the top level of the API skeleton.
"""

from .channel import Channel
from .controller import Controller, open_device, open_fake_device
from .errors import (
    ControllerClosedError,
    DeviceCommandError,
    DeviceConnectionError,
    DeviceNotFoundError,
    MightexLEDError,
    UnsupportedOperationError,
)
from .types import ControllerCapabilities, ModuleType, NormalParameters, OperatingMode

__all__ = [
    "Channel",
    "Controller",
    "ControllerCapabilities",
    "ControllerClosedError",
    "DeviceCommandError",
    "DeviceConnectionError",
    "DeviceNotFoundError",
    "MightexLEDError",
    "ModuleType",
    "NormalParameters",
    "OperatingMode",
    "UnsupportedOperationError",
    "open_device",
    "open_fake_device",
]
