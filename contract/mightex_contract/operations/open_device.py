"""open_device operation: open a connected controller by index."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components import ControllerCapabilities
from mightex_contract.errors import Error


class OpenDeviceRequest(ContractModel):
    """Open the controller at a discovery index."""

    index: int = Field(ge=0, description="Zero-based device index from a descriptor")


class OpenDeviceOk(ContractModel):
    """Successful open reply.

    Returns the full capabilities so the client has channel_count immediately
    (for example to bounds-check channel access) without a second round-trip.
    """

    status: Literal["ok"] = "ok"
    device_id: str = Field(description="Handle for subsequent operations")
    serial_number: str = Field(description="Serial number of the opened controller")
    capabilities: ControllerCapabilities = Field(
        description="Read-only capabilities of the opened controller"
    )


OpenDeviceReply = Annotated[
    Union[OpenDeviceOk, Error], Field(discriminator="status")
]
