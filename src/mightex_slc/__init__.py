# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: Public import surface for the mightex_slc library.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The public import surface of mightex_slc.

Everything here comes from the client package: open_device (or
open_fake_device, the explicit no-hardware path) returns a Controller, a
Controller hands out Channel proxies, the contract enums and the capabilities
model describe the device, and the MightexLEDError tree is the error
vocabulary. If a name is not importable from here, it is not part of the
public API.
"""

from .client import (
    Channel,
    Controller,
    ControllerCapabilities,
    ControllerClosedError,
    DeviceCommandError,
    DeviceConnectionError,
    DeviceNotFoundError,
    FollowerProfile,
    MightexLEDError,
    ModuleType,
    NormalParameters,
    OperatingMode,
    ProfileStep,
    StepProfile,
    TriggerParameters,
    TriggerPolarity,
    TriggerProfile,
    UnsupportedOperationError,
    open_device,
    open_fake_device,
)

__all__ = [
    "Channel",
    "Controller",
    "ControllerCapabilities",
    "ControllerClosedError",
    "DeviceCommandError",
    "DeviceConnectionError",
    "DeviceNotFoundError",
    "FollowerProfile",
    "MightexLEDError",
    "ModuleType",
    "NormalParameters",
    "OperatingMode",
    "ProfileStep",
    "StepProfile",
    "TriggerParameters",
    "TriggerPolarity",
    "TriggerProfile",
    "UnsupportedOperationError",
    "open_device",
    "open_fake_device",
]
