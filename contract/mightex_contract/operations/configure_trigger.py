"""configure_trigger operation: store TRIGGER mode parameters for a channel."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.trigger_polarity import TriggerPolarity
from mightex_contract.components.error_envelope import Error
from mightex_contract.operations.base import ChannelRequest
from mightex_contract.components.profile import Profile


class ConfigureTriggerRequest(ChannelRequest):
    """Store TRIGGER mode parameters for a channel.

    The number of profile steps must not exceed the module's max_profile_steps.
    That per-module limit is enforced server-side at runtime and does not export
    to JSON Schema; the static Profile bound is only the absolute 127-step
    ceiling. Trigger mode is unsupported on MA and CA modules, which the server
    reports as UnsupportedOperationError.
    """

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    polarity: TriggerPolarity = Field(
        default=TriggerPolarity.RISING,
        description="External trigger edge that asserts the profile",
    )
    profile: Profile = Field(
        description=(
            "Ordered profile steps without the terminating zero pair; the same "
            "rules as configure_strobe apply"
        )
    )


class ConfigureTriggerOk(ContractModel):
    """Successful configure-trigger reply."""

    status: Literal["ok"] = "ok"


ConfigureTriggerReply = Annotated[
    Union[ConfigureTriggerOk, Error], Field(discriminator="status")
]
