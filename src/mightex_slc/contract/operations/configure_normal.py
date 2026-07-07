# ------------------------------------------------------------------------------
#  Filename: configure_normal.py
#
#  Purpose: Define request and reply models for configuring NORMAL mode parameters.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, model_validator

from ..base import ContractModel
from ..components.error import Error
from .base import ChannelRequest


class ConfigureNormalRequest(ChannelRequest):
    """Set NORMAL-mode current parameters for a channel."""

    current_max_ma: float = Field(
        ge=0,
        description="NORMAL-mode current limit, in mA",
    )
    current_set_ma: float = Field(
        ge=0,
        description="NORMAL-mode set current, in mA",
    )

    @model_validator(mode="after")
    def _set_not_above_max(self) -> "ConfigureNormalRequest":
        if self.current_set_ma > self.current_max_ma:
            raise ValueError(
                "current_set_ma must be less than or equal to current_max_ma"
            )
        return self


class ConfigureNormalOk(ContractModel):
    """Configure-normal succeeded."""

    status: Literal["ok"] = "ok"


ConfigureNormalReply = Annotated[
    Union[ConfigureNormalOk, Error], Field(discriminator="status")
]
