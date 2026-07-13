# ------------------------------------------------------------------------------
#  Filename: get_trigger_parameters.py
#
#  Purpose: Define request and reply models for reading back TRIGGER-mode parameters.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from ..components.trigger_parameters import TriggerParameters
from .base import ChannelRequest


class GetTriggerParametersRequest(ChannelRequest):
    """Read back the stored TRIGGER-mode parameters of a channel."""


class GetTriggerParametersOk(ContractModel):
    """Successful get-trigger-parameters reply."""

    status: Literal["ok"] = "ok"
    result: TriggerParameters = Field(description="Stored TRIGGER-mode parameters of the channel")


GetTriggerParametersReply = Annotated[GetTriggerParametersOk | Error, Field(discriminator="status")]
