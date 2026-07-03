"""Reusable component models shared across operations.

Mirrors the contract/schemas/components/ layout. These models are the building
blocks (enums, error envelope, profile, shared device/parameter models) that
operation request/reply models compose.
"""

from __future__ import annotations

from mightex_contract.components.channel_state import ChannelState
from mightex_contract.components.controller_capabilities import ControllerCapabilities
from mightex_contract.components.device_descriptor import DeviceDescriptor
from mightex_contract.components.device_info import DeviceInfo
from mightex_contract.components.error import Error
from mightex_contract.components.error_type import ErrorType
from mightex_contract.components.module_type import ModuleType
from mightex_contract.components.normal_parameters import NormalParameters
from mightex_contract.components.operating_mode import OperatingMode
from mightex_contract.components.profile import Profile, ProfileStep
from mightex_contract.components.strobe_parameters import StrobeParameters
from mightex_contract.components.trigger_parameters import TriggerParameters
from mightex_contract.components.trigger_polarity import TriggerPolarity

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
