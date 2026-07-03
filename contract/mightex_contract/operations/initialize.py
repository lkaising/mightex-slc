"""initialize operation: put the controller into host control mode."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.error import Error
from mightex_contract.operations.base import DeviceRequest


class InitializeRequest(DeviceRequest):
    """Prepare the controller for host control."""


class InitializeOk(ContractModel):
    """Successful initialize reply."""

    status: Literal["ok"] = "ok"


InitializeReply = Annotated[
    Union[InitializeOk, Error], Field(discriminator="status")
]
