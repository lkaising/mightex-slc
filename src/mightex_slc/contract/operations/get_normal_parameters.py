# ------------------------------------------------------------------------------
#  Filename: get_normal_parameters.py
#
#  Purpose: Define request and reply models for reading back NORMAL-mode parameters.
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


class GetNormalParametersRequest(ChannelRequest):
    """Read back the stored NORMAL-mode parameters of a channel."""


class GetNormalParametersOk(ContractModel):
    """Successful get-normal-parameters reply."""

    status: Literal["ok"] = "ok"
    result: NormalParameters = Field(description="Stored NORMAL-mode parameters of the channel")


GetNormalParametersReply = Annotated[GetNormalParametersOk | Error, Field(discriminator="status")]
