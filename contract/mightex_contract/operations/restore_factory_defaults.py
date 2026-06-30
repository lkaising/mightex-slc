"""restore_factory_defaults operation: load factory defaults into settings."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.errors import Error
from mightex_contract.operations.base import DeviceRequest


class RestoreFactoryDefaultsRequest(DeviceRequest):
    """Load factory defaults into the current settings of all channels and modes.

    This changes current settings only; store_settings persists them.
    """


class RestoreFactoryDefaultsOk(ContractModel):
    """Successful restore-factory-defaults reply."""

    status: Literal["ok"] = "ok"


RestoreFactoryDefaultsReply = Annotated[
    Union[RestoreFactoryDefaultsOk, Error], Field(discriminator="status")
]
