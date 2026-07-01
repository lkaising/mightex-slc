"""configure_normal operation: store NORMAL mode parameters for a channel."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, model_validator

from mightex_contract.base import ContractModel
from mightex_contract.components.error_envelope import Error
from mightex_contract.operations.base import ChannelRequest


class ConfigureNormalRequest(ChannelRequest):
    """Store NORMAL mode parameters for a channel.

    Runtime-only rule (does not export to JSON Schema): current_set_ma must not
    exceed current_max_ma.
    """

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    current_set_ma: float = Field(ge=0, description="Working current in milliamps")

    @model_validator(mode="after")
    def _set_not_above_max(self) -> "ConfigureNormalRequest":
        # Runtime-only cross-field rule; does not export to JSON Schema.
        if self.current_set_ma > self.current_max_ma:
            raise ValueError("current_set_ma must not exceed current_max_ma")
        return self


class ConfigureNormalOk(ContractModel):
    """Successful configure-normal reply."""

    status: Literal["ok"] = "ok"


ConfigureNormalReply = Annotated[
    Union[ConfigureNormalOk, Error], Field(discriminator="status")
]
