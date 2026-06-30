"""Shape models read from or sent to the device.

Field names and units come straight from the public API skeleton.
"""

from __future__ import annotations

from pydantic import Field

from mightex_contract.base import ContractModel
from mightex_contract.enums import ModuleType, OperatingMode, TriggerPolarity
from mightex_contract.profile import Profile


class NormalParameters(ContractModel):
    """NORMAL mode parameters of a channel."""

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    current_set_ma: float = Field(ge=0, description="Working current in milliamps")


class StrobeParameters(ContractModel):
    """STROBE mode parameters of a channel."""

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    repeat_count: int = Field(
        ge=0,
        le=99999999,
        description=(
            "Device repeat count; the profile is output repeat_count + 1 times, "
            "or indefinitely when equal to REPEAT_FOREVER (9999)"
        ),
    )
    profile: Profile = Field(
        description="Ordered profile steps without the terminating zero pair"
    )


class TriggerParameters(ContractModel):
    """TRIGGER mode parameters of a channel."""

    current_max_ma: float = Field(ge=0, description="Maximum current in milliamps")
    polarity: TriggerPolarity = Field(
        description="External trigger edge that asserts the profile"
    )
    profile: Profile = Field(
        description="Ordered profile steps without the terminating zero pair"
    )


class ChannelState(ContractModel):
    """Snapshot of a channel read back from the device."""

    active_mode: OperatingMode = Field(
        description="The mode currently driving the channel output"
    )
    normal: NormalParameters = Field(description="Stored NORMAL mode parameters")
    strobe: StrobeParameters = Field(description="Stored STROBE mode parameters")
    trigger: TriggerParameters = Field(description="Stored TRIGGER mode parameters")


class DeviceInfo(ContractModel):
    """Identifying information reported by a controller."""

    device_type: str = Field(description="Module or device type string")
    firmware_version: str = Field(description="Firmware version string")
    serial_number: str = Field(description="Serial number string")
    raw: str = Field(description="Full information line exactly as reported")


class DeviceDescriptor(ContractModel):
    """Identity of a connected controller as seen during discovery.

    The documents expose only the number of connected controllers before a
    controller is opened. Serial number, module type, and channel count are read
    through functions that need an open device, so they are None here until the
    device is opened and are never guessed.
    """

    index: int = Field(ge=0, description="Zero-based device index for open_device")
    serial_number: str | None = Field(
        default=None, description="Serial number if readable before opening, else None"
    )
    module_type: ModuleType | None = Field(
        default=None, description="Module family if readable before opening, else None"
    )
    channel_count: int | None = Field(
        default=None,
        ge=1,
        description="Channel count if readable before opening, else None",
    )


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
