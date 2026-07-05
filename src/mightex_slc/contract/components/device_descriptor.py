# ------------------------------------------------------------------------------
#  Filename: device_descriptor.py
#
#  Purpose: Define discovery-time identity data for a connected controller.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from pydantic import Field

from ..base import ContractModel
from .module_type import ModuleType


class DeviceDescriptor(ContractModel):
    """Identity of a connected controller as seen during discovery.

    Only the number of connected controllers is knowable before a controller
    is opened. Serial number, module type, and channel count are read through
    functions that need an open device, so they are None here until the device
    is opened and are never guessed.
    """

    index: int = Field(ge=0, description="Zero-based device index for open_device")
    serial_number: str | None = Field(
        default=None, description="Serial number if readable before opening, else None"
    )
    module_type: ModuleType | None = Field(
        default=None, description="Module family if readable before opening, else None"
    )
    channel_count: int | None = Field(
        default=None,
        ge=1,
        description="Channel count if readable before opening, else None",
    )
