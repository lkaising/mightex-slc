# ------------------------------------------------------------------------------
#  Filename: get_active_mode.py
#
#  Purpose: Define request and reply models for retrieving a channel's active mode.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from ..components.operating_mode import OperatingMode
from .base import ChannelRequest


class GetActiveModeRequest(ChannelRequest):
    """Read back the mode currently driving a channel."""


class GetActiveModeOk(ContractModel):
    """Successful get-active-mode reply."""

    status: Literal["ok"] = "ok"
    result: OperatingMode = Field(description="The mode currently driving the channel")


GetActiveModeReply = Annotated[GetActiveModeOk | Error, Field(discriminator="status")]
