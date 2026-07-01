"""DeviceInfo: identifying information reported by a controller.

Field names and units come straight from the public API skeleton.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel


class DeviceInfo(ContractModel):
    """Identifying information reported by a controller."""

    device_type: str = Field(description="Module or device type string")
    firmware_version: str = Field(description="Firmware version string")
    serial_number: str = Field(description="Serial number string")
    raw: str = Field(description="Full information line exactly as reported")
