"""set_fan_pwm_level operation: set the cooling fan drive level."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.error_envelope import Error
from mightex_contract.operations.base import DeviceRequest


class SetFanPwmLevelRequest(DeviceRequest):
    """Set the cooling fan drive level."""

    level: int = Field(
        ge=0,
        le=10,
        description="Fan drive level, 0 fully off to 10 fully on, in 10 percent steps",
    )


class SetFanPwmLevelOk(ContractModel):
    """Successful set-fan-pwm-level reply."""

    status: Literal["ok"] = "ok"


SetFanPwmLevelReply = Annotated[
    Union[SetFanPwmLevelOk, Error], Field(discriminator="status")
]
