# ------------------------------------------------------------------------------
#  Filename: get_trigger_profile.py
#
#  Purpose: Define request and reply models for reading back a channel's trigger profile.
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


class GetTriggerProfileRequest(ChannelRequest):
    """Read back the stored trigger profile of a channel."""


class GetTriggerProfileOk(ContractModel):
    """Successful get-trigger-profile reply."""

    status: Literal["ok"] = "ok"
    result: TriggerProfile = Field(description="Stored trigger profile of the channel")


GetTriggerProfileReply = Annotated[GetTriggerProfileOk | Error, Field(discriminator="status")]
