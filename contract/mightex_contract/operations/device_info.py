"""device_info operation: query identifying information from a controller."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.shared_models import DeviceInfo
from mightex_contract.components.errors import Error
from mightex_contract.operations.base import DeviceRequest


class DeviceInfoRequest(DeviceRequest):
    """Request identifying information from an open controller."""


class DeviceInfoOk(ContractModel):
    """Successful device-info reply."""

    status: Literal["ok"] = "ok"
    result: DeviceInfo = Field(
        description="Identifying information reported by the controller"
    )


DeviceInfoReply = Annotated[
    Union[DeviceInfoOk, Error], Field(discriminator="status")
]
