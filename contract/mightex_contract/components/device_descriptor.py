"""DeviceDescriptor: identity of a connected controller as seen during discovery.

Field names and units come straight from the public API skeleton.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.module_type import ModuleType


class DeviceDescriptor(ContractModel):
    """Identity of a connected controller as seen during discovery.

    The documents expose only the number of connected controllers before a
    controller is opened. Serial number, module type, and channel count are read
    through functions that need an open device, so they are None here until the
    device is opened and are never guessed.
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
