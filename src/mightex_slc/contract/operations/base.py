# ------------------------------------------------------------------------------
#  Filename: base.py
#
#  Purpose: Define shared request bases for device and channel operations.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from pydantic import Field

from ..base import ContractModel


class DeviceRequest(ContractModel):
    """Base request for device-level operations."""

    device_id: str = Field(description="Handle returned by open_device")


class ChannelRequest(DeviceRequest):
    """Base request for channel-level operations."""

    channel: int = Field(ge=1, description="One-based channel number")
