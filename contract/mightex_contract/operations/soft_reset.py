"""soft_reset operation: perform a soft reset of the controller."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.errors import Error
from mightex_contract.operations.base import DeviceRequest


class SoftResetRequest(DeviceRequest):
    """Perform a soft reset of the controller."""


class SoftResetOk(ContractModel):
    """Successful soft-reset reply."""

    status: Literal["ok"] = "ok"


SoftResetReply = Annotated[
    Union[SoftResetOk, Error], Field(discriminator="status")
]
