# ------------------------------------------------------------------------------
#  Filename: profiles.py
#
#  Purpose: Define the profile shapes the pulsed modes store and play back.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
Profile models for the pulsed modes.

ProfileStep and StepProfile are deliberately mode-neutral: STROBE profiles
have the same step semantics on the wire, so a future STROBE slice reuses
them unchanged. FollowerProfile and the TriggerProfile union are
trigger-only — follower mode has no STROBE counterpart.
"""

from __future__ import annotations

from typing import Annotated, Final, Literal

from pydantic import Field, model_validator

from ..base import ContractModel

# Wire-reserved duration: the device reinterprets a *first* profile step with
# this Tset as follower mode rather than as a timed step. Public models never
# carry it — FollowerProfile is the explicit spelling, and the codec is the
# only place the sentinel appears on the wire.
FOLLOWER_SENTINEL_DURATION_US: Final[int] = 9999


class ProfileStep(ContractModel):
    """One timed step of a profile: drive a current for a duration."""

    current_ma: float = Field(ge=0, description="Step drive current, in mA")
    duration_us: int = Field(ge=1, le=99_999_999, description="Step duration, in microseconds")


class StepProfile(ContractModel):
    """An ordinary profile: a sequence of timed steps, played in order.

    An empty profile is valid and means the channel does nothing on trigger —
    the device's own cleared state, and the way to clear a stored profile.
    The wire-level (0, 0) terminator step is not part of the model; the codec
    appends it. How many steps a given controller can store is a module
    capability, enforced where capabilities are known.
    """

    kind: Literal["steps"] = "steps"
    steps: tuple[ProfileStep, ...] = Field(
        max_length=127, description="Timed steps, played in wire order"
    )

    @model_validator(mode="after")
    def _first_step_is_not_the_follower_sentinel(self) -> StepProfile:
        if self.steps and self.steps[0].duration_us == FOLLOWER_SENTINEL_DURATION_US:
            raise ValueError(
                f"a first step of {FOLLOWER_SENTINEL_DURATION_US} us is reserved: the device "
                "would silently play it as follower mode; use FollowerProfile to ask for that"
            )
        return self


class FollowerProfile(ContractModel):
    """A trigger-only profile: the output follows the trigger input level.

    While the trigger input is asserted the channel drives current_ma;
    otherwise it is off. This is the explicit spelling of the device's
    reserved first-step duration, which never appears in a public field.
    """

    kind: Literal["follower"] = "follower"
    current_ma: float = Field(
        ge=0, description="Drive current while the trigger input is asserted, in mA"
    )


TriggerProfile = Annotated[StepProfile | FollowerProfile, Field(discriminator="kind")]
"""What a channel's trigger profile storage can hold: steps or follower."""
