# ------------------------------------------------------------------------------
#  Filename: close_device.py
#
#  Purpose: Define request and reply models for closing a device handle.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from .base import DeviceRequest


class CloseDeviceRequest(DeviceRequest):
    """Close an opened controller."""


class CloseDeviceOk(ContractModel):
    """Controller closed successfully."""

    status: Literal["ok"] = "ok"


CloseDeviceReply = Annotated[Union[CloseDeviceOk, Error], Field(discriminator="status")]
