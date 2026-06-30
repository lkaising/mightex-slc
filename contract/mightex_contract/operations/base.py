"""Shared request bases for operation models.

DeviceRequest carries the device handle; ChannelRequest adds the one-based
channel. Both inherit extra="forbid" and frozen=True from ContractModel.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel


class DeviceRequest(ContractModel):
    """Base request for device-level operations."""

    device_id: str = Field(description="Handle returned by open_device")


class ChannelRequest(DeviceRequest):
    """Base request for channel-level operations."""

    channel: int = Field(ge=1, description="One-based channel number")
