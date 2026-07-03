"""store_settings operation: write current settings to non-volatile memory."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.error import Error
from mightex_contract.operations.base import DeviceRequest


class StoreSettingsRequest(DeviceRequest):
    """Persist the current settings of all channels and modes."""


class StoreSettingsOk(ContractModel):
    """Successful store-settings reply."""

    status: Literal["ok"] = "ok"


StoreSettingsReply = Annotated[
    Union[StoreSettingsOk, Error], Field(discriminator="status")
]
