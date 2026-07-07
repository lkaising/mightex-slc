# ------------------------------------------------------------------------------
#  Filename: controller_capabilities.py
#
#  Purpose: Define read-only capabilities reported by an open controller.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from pydantic import Field

from ..base import ContractModel
from .module_type import ModuleType


class ControllerCapabilities(ContractModel):
    """Read-only limits and feature flags for an opened controller.

    Returned by the server so clients can choose valid operations without
    duplicating vendor module tables.
    """

    module_type: ModuleType = Field(description="Controller module family.")
    channel_count: int = Field(ge=1, description="Number of LED output channels.")
    current_resolution_ma: float = Field(
        gt=0, description="Smallest settable current increment, in milliamps."
    )
    max_profile_steps: int = Field(
        ge=2,
        le=127,
        description=(
            "Maximum programmable current/time pairs before the required "
            "(0, 0) terminator."
        ),
    )
    supports_trigger_mode: bool = Field(
        description="Whether TRIGGER mode is available."
    )
    supports_load_voltage: bool = Field(
        description="Whether load-voltage read-back is available."
    )
    supports_fan_control: bool = Field(
        description="Whether FanPWM control is available."
    )
