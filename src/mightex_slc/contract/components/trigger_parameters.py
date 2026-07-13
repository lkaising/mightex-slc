# ------------------------------------------------------------------------------
#  Filename: trigger_parameters.py
#
#  Purpose: Define the TRIGGER-mode parameter pair a channel stores and reports.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from pydantic import Field

from ..base import ContractModel
from .trigger_polarity import TriggerPolarity


class TriggerParameters(ContractModel):
    """TRIGGER-mode parameter pair for one channel.

    Stored independently of the trigger profile: this pair caps the profile's
    step currents and selects the trigger edge, while the profile holds the
    steps themselves. The device silently clamps an over-ceiling limit instead
    of rejecting it, so an acknowledged write is not proof of what was stored —
    read back to verify.
    """

    current_max_ma: float = Field(ge=0, description="TRIGGER-mode current limit, in mA")
    polarity: TriggerPolarity = Field(description="Trigger input edge that starts playback")
