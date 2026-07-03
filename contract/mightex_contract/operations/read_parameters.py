"""read_parameters operation: read all stored mode parameters and active mode."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.channel_state import ChannelState
from mightex_contract.components.error import Error
from mightex_contract.operations.base import ChannelRequest


class ReadParametersRequest(ChannelRequest):
    """Read back the stored parameters of all modes and the active mode."""


class ReadParametersOk(ContractModel):
    """Successful read-parameters reply."""

    status: Literal["ok"] = "ok"
    result: ChannelState = Field(
        description="Snapshot of all mode parameters and the active mode"
    )


ReadParametersReply = Annotated[
    Union[ReadParametersOk, Error], Field(discriminator="status")
]
