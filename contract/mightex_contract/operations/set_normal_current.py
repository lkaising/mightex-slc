"""set_normal_current operation: set the NORMAL mode working current only."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.errors import Error
from mightex_contract.operations.base import ChannelRequest


class SetNormalCurrentRequest(ChannelRequest):
    """Set only the NORMAL mode working current, leaving the maximum unchanged."""

    current_ma: float = Field(ge=0, description="Working current in milliamps")


class SetNormalCurrentOk(ContractModel):
    """Successful set-normal-current reply."""

    status: Literal["ok"] = "ok"


SetNormalCurrentReply = Annotated[
    Union[SetNormalCurrentOk, Error], Field(discriminator="status")
]
