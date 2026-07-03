"""Pydantic source-of-truth contract for the Mightex SLC LED controller library.

This package is the single source of truth and the single validator at the
client/server seam. The client re-exports these models rather than mirroring
them by hand, and the server validates against them. The YAML/JSON Schema files
under contract/schemas/ are generated from these models by generate_schemas.py.

Operation request and reply models live in the operations subpackage and are
imported from mightex_contract.operations.
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
from mightex_contract.constants import REPEAT_FOREVER

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
