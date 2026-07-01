"""configure_strobe operation: store STROBE mode parameters for a channel."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.error_envelope import Error
from mightex_contract.operations.base import ChannelRequest
from mightex_contract.components.profile import Profile


class ConfigureStrobeRequest(ChannelRequest):
    """Store STROBE mode parameters for a channel.

    The number of profile steps must not exceed the module's max_profile_steps.
    That per-module limit is enforced server-side at runtime and does not export
    to JSON Schema; the static Profile bound is only the absolute 127-step
    ceiling.
    """

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    repeat_count: int = Field(
        default=0,
        ge=0,
        le=99999999,
        description=(
            "Device repeat count; the profile is output repeat_count + 1 times, "
            "or indefinitely when equal to REPEAT_FOREVER (9999). Defaults to 0, "
            "which outputs the profile once."
        ),
    )
    profile: Profile = Field(
        description=(
            "Ordered profile steps without the terminating zero pair; an empty "
            "profile leaves the channel off in STROBE mode"
        )
    )


class ConfigureStrobeOk(ContractModel):
    """Successful configure-strobe reply."""

    status: Literal["ok"] = "ok"


ConfigureStrobeReply = Annotated[
    Union[ConfigureStrobeOk, Error], Field(discriminator="status")
]
