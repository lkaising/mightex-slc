"""Strobe and trigger profile types.

A profile is an ordered sequence of steps, each a current held for a duration.
The terminating zero pair handled by the device is never represented here.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from mightex_contract.base import ContractModel


class ProfileStep(ContractModel):
    """A single profile step.

    Note: the public API skeleton expresses a step as a bare tuple
    (current_ma, time_us). The contract deliberately replaces that tuple with
    this named model, so the serialized form is
    {"current_ma": 10.0, "time_us": 1000} rather than [10.0, 1000]. That object
    form is the intended public surface.
    """

    current_ma: float = Field(ge=0, description="Step current in milliamps")
    time_us: int = Field(ge=0, description="Step duration in whole microseconds")


# Profile carries an absolute upper bound of 127 steps. This 127 is a library
# guard (the documented absolute ceiling for full-profile modules), not the
# per-module limit. The documents give 127 only for full-profile modules and as
# few as 2 for modules they call limited. The real per-module check
# (len(profile) <= Controller.max_profile_steps) is enforced server-side at
# runtime and does not export to JSON Schema. No minimum length is set, because
# an empty profile is valid and leaves the channel off. The terminating zero
# pair is never included.
Profile = Annotated[list[ProfileStep], Field(max_length=127)]
