"""NormalParameters: NORMAL mode parameters of a channel.

Field names and units come straight from the public API skeleton.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel


class NormalParameters(ContractModel):
    """NORMAL mode parameters of a channel."""

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    current_set_ma: float = Field(ge=0, description="Working current in milliamps")
