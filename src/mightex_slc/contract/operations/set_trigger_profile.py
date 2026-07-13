# ------------------------------------------------------------------------------
#  Filename: set_trigger_profile.py
#
#  Purpose: Define request and reply models for storing a channel's trigger profile.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from ..components.profiles import TriggerProfile
from .base import ChannelRequest


class SetTriggerProfileRequest(ChannelRequest):
    """Store a trigger profile for a channel."""

    profile: TriggerProfile = Field(description="Trigger profile to store")


class SetTriggerProfileOk(ContractModel):
    """Set-trigger-profile succeeded."""

    status: Literal["ok"] = "ok"


SetTriggerProfileReply = Annotated[SetTriggerProfileOk | Error, Field(discriminator="status")]
