"""close_device operation: close a device handle and release it."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.error import Error
from mightex_contract.operations.base import DeviceRequest


class CloseDeviceRequest(DeviceRequest):
    """Close the controller handle and release it."""

    # TODO (provisional): mapping Controller.close() and the context-manager
    # __exit__ onto this single close operation. The client proxy is stateless
    # and the server owns the handle, so both client-side paths route here.


class CloseDeviceOk(ContractModel):
    """Successful close reply."""

    status: Literal["ok"] = "ok"


CloseDeviceReply = Annotated[
    Union[CloseDeviceOk, Error], Field(discriminator="status")
]
