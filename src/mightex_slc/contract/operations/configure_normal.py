# ------------------------------------------------------------------------------
#  Filename: configure_normal.py
#
#  Purpose: Define request and reply models for configuring NORMAL mode parameters.
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


class ConfigureNormalRequest(ChannelRequest):
    """Set NORMAL-mode current parameters for a channel."""

    parameters: NormalParameters = Field(description="NORMAL-mode current parameters to store")


class ConfigureNormalOk(ContractModel):
    """Configure-normal succeeded."""

    status: Literal["ok"] = "ok"


ConfigureNormalReply = Annotated[ConfigureNormalOk | Error, Field(discriminator="status")]
