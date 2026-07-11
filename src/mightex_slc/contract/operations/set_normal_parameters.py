# ------------------------------------------------------------------------------
#  Filename: set_normal_parameters.py
#
#  Purpose: Define request and reply models for setting NORMAL mode parameters.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from ..components.normal_parameters import NormalParameters
from .base import ChannelRequest


class SetNormalParametersRequest(ChannelRequest):
    """Set NORMAL-mode current parameters for a channel."""

    parameters: NormalParameters = Field(description="NORMAL-mode current parameters to store")


class SetNormalParametersOk(ContractModel):
    """Set-normal-parameters succeeded."""

    status: Literal["ok"] = "ok"


SetNormalParametersReply = Annotated[SetNormalParametersOk | Error, Field(discriminator="status")]
