"""Pydantic source-of-truth contract for the Mightex SLC LED controller library.

This package is the single source of truth and the single validator at the
client/server seam. The client re-exports these models rather than mirroring
them by hand, and the server validates against them. The YAML/JSON Schema files
under contract/schemas/ are generated from these models by generate_schemas.py.

Operation request and reply models live in the operations subpackage and are
imported from mightex_contract.operations.
"""

from __future__ import annotations

from mightex_contract.components.shared_models import (
    ChannelState,
    ControllerCapabilities,
    DeviceDescriptor,
    DeviceInfo,
    NormalParameters,
    StrobeParameters,
    TriggerParameters,
)
from mightex_contract.constants import REPEAT_FOREVER
from mightex_contract.components.enums import ModuleType, OperatingMode, TriggerPolarity
from mightex_contract.components.errors import Error, ErrorType
from mightex_contract.components.profile import Profile, ProfileStep

__all__ = [
    # constant
    "REPEAT_FOREVER",
    # enums
    "OperatingMode",
    "TriggerPolarity",
    "ModuleType",
    # profile
    "ProfileStep",
    "Profile",
    # shared models
    "NormalParameters",
    "StrobeParameters",
    "TriggerParameters",
    "ChannelState",
    "DeviceInfo",
    "DeviceDescriptor",
    "ControllerCapabilities",
    # error envelope
    "ErrorType",
    "Error",
]
