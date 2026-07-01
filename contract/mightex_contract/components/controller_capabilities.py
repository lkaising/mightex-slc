"""ControllerCapabilities: aggregated read-only capabilities of an open controller.

Field names and units come straight from the public API skeleton.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.components.module_type import ModuleType


class ControllerCapabilities(ContractModel):
    """Aggregated read-only capabilities of an open controller.

    These fields are device truth sent server-to-client, so the le and gt bounds
    below are sanity guards on a trusted source, not request validation.
    """

    # TODO (provisional): the skeleton exposes these as separate Controller
    # read-only properties. Bundling them into one model for the get_capabilities
    # reply and the open_device reply is a contract design choice. This model
    # deliberately excludes serial_number (identity, served by the open_device
    # reply), is_closed (client-side state), and channels (client-side handles).
    module_type: ModuleType = Field(description="Module family of this controller")
    channel_count: int = Field(ge=1, description="Number of output channels")
    current_resolution_ma: float = Field(
        gt=0,
        description=(
            "Current step size in milliamps. The documents state 1.0 for AA, AV, "
            "SA, SV, HA, HV, MA, and CA modules and 0.1 for FA, FV, XA, and XV "
            "modules. The documents do not state a resolution for QA, so any QA "
            "value is a server-side library convention, not a device fact."
        ),
    )
    max_profile_steps: int = Field(
        ge=2,
        le=127,
        description=(
            "Maximum usable profile steps, not counting the terminating zero "
            "pair. The documents give 127 for full-profile modules and as few as "
            "2 for modules they call limited."
        ),
    )
    supports_trigger_mode: bool = Field(
        description="Whether this module supports TRIGGER mode; False for MA and CA"
    )
    supports_load_voltage: bool = Field(
        description="Whether this module supports load voltage read-back"
    )
    supports_fan_control: bool = Field(
        description="Whether this module exposes fan control"
    )
    requires_initialization: bool = Field(
        description="Whether this module must be prepared with initialize() first"
    )
