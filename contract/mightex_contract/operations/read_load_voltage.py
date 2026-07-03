"""read_load_voltage operation: read the present load voltage on a channel."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.error import Error
from mightex_contract.operations.base import ChannelRequest


class ReadLoadVoltageRequest(ChannelRequest):
    """Read the present load voltage on a channel.

    Load voltage read-back is a voltage-monitoring module variant feature; on
    modules without it the server reports UnsupportedOperationError. The reading
    is meaningful only in NORMAL mode or a slow STROBE mode, because the
    controller polls the load at a 20 ms interval.
    """


class ReadLoadVoltageOk(ContractModel):
    """Successful read-load-voltage reply."""

    status: Literal["ok"] = "ok"
    result: int = Field(description="Present load voltage in millivolts")


ReadLoadVoltageReply = Annotated[
    Union[ReadLoadVoltageOk, Error], Field(discriminator="status")
]
