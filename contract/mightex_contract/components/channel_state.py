"""ChannelState: snapshot of a channel read back from the device.

Field names and units come straight from the public API skeleton.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.normal_parameters import NormalParameters
from mightex_contract.components.operating_mode import OperatingMode
from mightex_contract.components.strobe_parameters import StrobeParameters
from mightex_contract.components.trigger_parameters import TriggerParameters


class ChannelState(ContractModel):
    """Snapshot of a channel read back from the device."""

    active_mode: OperatingMode = Field(
        description="The mode currently driving the channel output"
    )
    normal: NormalParameters = Field(description="Stored NORMAL mode parameters")
    strobe: StrobeParameters = Field(description="Stored STROBE mode parameters")
    trigger: TriggerParameters = Field(description="Stored TRIGGER mode parameters")
