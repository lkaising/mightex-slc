"""get_active_mode operation: read back the mode driving a channel."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.operating_mode import OperatingMode
from mightex_contract.components.error import Error
from mightex_contract.operations.base import ChannelRequest


class GetActiveModeRequest(ChannelRequest):
    """Read back the mode currently driving a channel."""


class GetActiveModeOk(ContractModel):
    """Successful get-active-mode reply."""

    status: Literal["ok"] = "ok"
    result: OperatingMode = Field(
        description="The mode currently driving the channel"
    )


GetActiveModeReply = Annotated[
    Union[GetActiveModeOk, Error], Field(discriminator="status")
]
