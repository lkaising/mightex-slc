# ------------------------------------------------------------------------------
#  Filename: open_device.py
#
#  Purpose: Define request and reply models for opening a controller.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from ..base import ContractModel
from ..components.controller_capabilities import ControllerCapabilities
from ..components.error import Error


class OpenDeviceRequest(ContractModel):
    """Open the controller at a serial port."""

    port: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Serial port device path of the controller to open "
            "(e.g. /dev/cu.usbserial-A6002xyz); None uses the backend's "
            "configured default target"
        ),
    )


class OpenDeviceOk(ContractModel):
    """Controller opened successfully."""

    status: Literal["ok"] = "ok"
    device_id: str = Field(
        description="Opaque device id for subsequent operations"
    )
    serial_number: str = Field(
        description="Serial number of the opened controller"
    )
    capabilities: ControllerCapabilities = Field(
        description="Capabilities of the opened controller"
    )


OpenDeviceReply = Annotated[
    Union[OpenDeviceOk, Error], Field(discriminator="status")
]
