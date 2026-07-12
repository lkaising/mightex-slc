# ------------------------------------------------------------------------------
#  Filename: normal_parameters.py
#
#  Purpose: Define the NORMAL-mode parameter pair a channel stores and reports.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from pydantic import Field, model_validator

from ..base import ContractModel


class NormalParameters(ContractModel):
    """NORMAL-mode current parameter pair for one channel."""

    current_max_ma: float = Field(ge=0, description="NORMAL-mode current limit, in mA")
    current_set_ma: float = Field(ge=0, description="NORMAL-mode set current, in mA")

    @model_validator(mode="after")
    def _set_not_above_max(self) -> NormalParameters:
        if self.current_set_ma > self.current_max_ma:
            raise ValueError("current_set_ma must be less than or equal to current_max_ma")
        return self
