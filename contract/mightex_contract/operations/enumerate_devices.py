"""enumerate_devices operation: discover connected controllers."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.shared_models import DeviceDescriptor
from mightex_contract.components.errors import Error


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
