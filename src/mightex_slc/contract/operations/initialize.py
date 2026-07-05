# ------------------------------------------------------------------------------
#  Filename: initialize.py
#
#  Purpose: Define request and reply models for preparing a controller for host control.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from .base import DeviceRequest


class InitializeRequest(DeviceRequest):
    """Prepare the controller for host control."""


class InitializeOk(ContractModel):
    """Successful initialize reply."""

    status: Literal["ok"] = "ok"


InitializeReply = Annotated[Union[InitializeOk, Error], Field(discriminator="status")]
