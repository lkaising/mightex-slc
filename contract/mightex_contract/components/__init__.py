"""Reusable component models shared across operations.

Mirrors the contract/schemas/components/ layout. These models are the building
blocks (enums, error envelope, profile, shared device/parameter models) that
operation request/reply models compose.
"""

from __future__ import annotations

from mightex_contract.components.enums import ModuleType, OperatingMode, TriggerPolarity
from mightex_contract.components.errors import Error, ErrorType
from mightex_contract.components.profile import Profile, ProfileStep
from mightex_contract.components.shared_models import (
    ChannelState,
    ControllerCapabilities,
    DeviceDescriptor,
    DeviceInfo,
    NormalParameters,
    StrobeParameters,
    TriggerParameters,
)

__all__ = [
    # enums
    "OperatingMode",
    "TriggerPolarity",
    "ModuleType",
    # error envelope
    "ErrorType",
    "Error",
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
]
