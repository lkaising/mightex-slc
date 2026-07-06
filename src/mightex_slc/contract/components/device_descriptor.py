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
    """Identity data for a discovered controller.

    The SDK discovers controllers by count and opens them by zero-based index.
    Serial number, module family, and channel count require an open device handle,
    so they may be None in discovery-only responses.
    """

    index: int = Field(
        ge=0,
        description="Discovery-session index for open_device"
    )
    serial_number: str | None = Field(
        default=None,
        description="Controller serial number, when resolved.",
    )
    module_type: ModuleType | None = Field(
        default=None,
        description="Controller module family, when resolved.",
    )
    channel_count: int | None = Field(
        default=None,
        ge=1,
        description="Number of output channels, when resolved.",
    )
