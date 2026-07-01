"""TriggerParameters: TRIGGER mode parameters of a channel.

Field names and units come straight from the public API skeleton.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.profile import Profile
from mightex_contract.components.trigger_polarity import TriggerPolarity


class TriggerParameters(ContractModel):
    """TRIGGER mode parameters of a channel."""

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    polarity: TriggerPolarity = Field(
        description="External trigger edge that asserts the profile"
    )
    profile: Profile = Field(
        description="Ordered profile steps without the terminating zero pair"
    )
