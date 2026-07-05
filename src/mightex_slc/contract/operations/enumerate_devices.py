# ------------------------------------------------------------------------------
#  Filename: enumerate_devices.py
#
#  Purpose: Define request and reply models for discovering connected controllers.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from ..base import ContractModel
from ..components.device_descriptor import DeviceDescriptor
from ..components.error import Error


class EnumerateDevicesRequest(ContractModel):
    """Request to scan for connected controllers. Carries no fields."""


class EnumerateDevicesOk(ContractModel):
    """Successful discovery reply."""

    status: Literal["ok"] = "ok"
    result: list[DeviceDescriptor] = Field(
        description="One descriptor per connected controller, in index order"
    )


EnumerateDevicesReply = Annotated[
    Union[EnumerateDevicesOk, Error], Field(discriminator="status")
]
