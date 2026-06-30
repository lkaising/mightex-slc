"""get_capabilities operation: read a controller's read-only capabilities."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.shared_models import ControllerCapabilities
from mightex_contract.components.errors import Error
from mightex_contract.operations.base import DeviceRequest


class GetCapabilitiesRequest(DeviceRequest):
    """Request the capabilities of an open controller."""


class GetCapabilitiesOk(ContractModel):
    """Successful capabilities reply."""

    status: Literal["ok"] = "ok"
    result: ControllerCapabilities = Field(
        description="Read-only capabilities of the controller"
    )


GetCapabilitiesReply = Annotated[
    Union[GetCapabilitiesOk, Error], Field(discriminator="status")
]
