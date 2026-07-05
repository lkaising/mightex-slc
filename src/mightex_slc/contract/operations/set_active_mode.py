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
    """Select the active working mode for a channel."""

    mode: OperatingMode = Field(description="The mode to make active")


class SetActiveModeOk(ContractModel):
    """Successful set-active-mode reply."""

    status: Literal["ok"] = "ok"


SetActiveModeReply = Annotated[
    Union[SetActiveModeOk, Error], Field(discriminator="status")
]
