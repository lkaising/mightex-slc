"""StrobeParameters: STROBE mode parameters of a channel.

Field names and units come straight from the public API skeleton.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.profile import Profile


class StrobeParameters(ContractModel):
    """STROBE mode parameters of a channel."""

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    repeat_count: int = Field(
        ge=0,
        le=99999999,
        description=(
            "Device repeat count; the profile is output repeat_count + 1 times, "
            "or indefinitely when equal to REPEAT_FOREVER (9999)"
        ),
    )
    profile: Profile = Field(
        description="Ordered profile steps without the terminating zero pair"
    )
