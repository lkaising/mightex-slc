# ------------------------------------------------------------------------------
#  Filename: normal_parameters.py
#
#  Purpose: Define the stored NORMAL-mode parameter pair reported by a channel.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from pydantic import Field

from ..base import ContractModel


class NormalParameters(ContractModel):
    """Stored NORMAL-mode current parameters, as one channel reports them."""

    current_max_ma: float = Field(ge=0, description="Stored NORMAL-mode current limit, in mA")
    current_set_ma: float = Field(ge=0, description="Stored NORMAL-mode set current, in mA")
