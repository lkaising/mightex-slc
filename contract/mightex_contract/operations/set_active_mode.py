"""set_active_mode operation: select the active working mode for a channel."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.enums import OperatingMode
from mightex_contract.errors import Error
from mightex_contract.operations.base import ChannelRequest


class SetActiveModeRequest(ChannelRequest):
    """Select the active working mode for a channel."""

    mode: OperatingMode = Field(description="The mode to make active")


class SetActiveModeOk(ContractModel):
    """Successful set-active-mode reply."""

    status: Literal["ok"] = "ok"


SetActiveModeReply = Annotated[
    Union[SetActiveModeOk, Error], Field(discriminator="status")
]
