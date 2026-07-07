# ------------------------------------------------------------------------------
#  Filename: set_active_mode.py
#
#  Purpose: Define request and reply models for selecting a channel's active mode.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from ..components.operating_mode import OperatingMode
from .base import ChannelRequest


class SetActiveModeRequest(ChannelRequest):
    """Switch a channel to an active working mode."""

    mode: OperatingMode = Field(description="Working mode to select")


class SetActiveModeOk(ContractModel):
    """Active mode changed successfully."""

    status: Literal["ok"] = "ok"


SetActiveModeReply = Annotated[Union[SetActiveModeOk, Error], Field(discriminator="status")]
