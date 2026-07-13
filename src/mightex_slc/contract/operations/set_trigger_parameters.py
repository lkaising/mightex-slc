# ------------------------------------------------------------------------------
#  Filename: set_trigger_parameters.py
#
#  Purpose: Define request and reply models for setting TRIGGER mode parameters.
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


class SetTriggerParametersRequest(ChannelRequest):
    """Set TRIGGER-mode parameters for a channel."""

    parameters: TriggerParameters = Field(description="TRIGGER-mode parameters to store")


class SetTriggerParametersOk(ContractModel):
    """Set-trigger-parameters succeeded."""

    status: Literal["ok"] = "ok"


SetTriggerParametersReply = Annotated[SetTriggerParametersOk | Error, Field(discriminator="status")]
