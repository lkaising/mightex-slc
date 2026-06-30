"""Public API skeleton for the Mightex Sirius Multi-Channel LED Controller
(SLC-XXXX-S/U family).

This module defines only the public surface: classes, enums, constants, type
hints, and docstrings. Method bodies are not implemented.

Design rationale
================

Object model
    A connected controller is a ``Controller`` object that owns its channels.
    Channel-specific operations live on a ``Channel`` object obtained with
    ``Controller.channel(n)``. A channel accessor returns a live handle bound
    to that channel, not a snapshot. Repeated access to the same channel number
    returns the same ``Channel`` object. Using a controller or channel after
    the controller is closed raises ``ControllerClosedError``. Device-wide
    operations (persistence, reset, device information, fan control,
    initialization) live on ``Controller``. This fits the device, where each
    channel independently holds its own normal, strobe, and trigger parameters
    plus its own active mode.

Discovery and lifecycle
    ``enumerate_devices()`` returns one ``DeviceDescriptor`` per connected
    controller and must be called before opening. Each descriptor carries the
    zero-based index used to open that controller. ``open_device(index)`` opens
    one controller by index and returns a ``Controller``.
    ``Controller.close()`` releases it, and ``Controller`` supports the context
    manager protocol so it can be used in a ``with`` block.

    The documents expose only the number of connected controllers at discovery
    time. Identity such as serial number, module type, and channel count is read
    through functions that need an open device, so a descriptor reports those
    fields as unavailable until the controller is opened.

Channel indexing
    Channels are one-based, matching the device and the hardware labels.
    ``Channel.number`` is the one-based index. Every method that takes or
    returns a channel number uses one-based numbering, stated again at each
    method.

Current units and resolution
    All current values cross the API boundary as milliamps (float). The
    documents give two resolution groups: 1 mA for AA, AV, SA, SV, HA, HV, MA,
    and CA modules, and 0.1 mA for FA, FV, XA, and XV modules. The documents do
    not state a resolution for QA modules. A requested current is rounded to the
    nearest representable step. Read ``Controller.current_resolution_ma`` to
    learn the step for the connected module. Profile time values are integers in
    microseconds.

Operating modes
    DISABLE, NORMAL, STROBE, and TRIGGER are an enum (``OperatingMode``). The
    parameters for a mode can be configured while that mode is not the active
    mode. Physical output does not change until the mode becomes active via
    ``Channel.set_active_mode()``.

Strobe and trigger profiles
    A profile is a Python sequence of ``(current_ma, time_us)`` pairs. The
    terminating zero pair is handled internally and must not be supplied by the
    caller. The maximum number of usable steps depends on the module and is
    reported by ``Controller.max_profile_steps`` (127 on modules that allow the
    full profile, and as few as 2 on modules the documents describe as limited).
    The strobe repeat count uses the device convention: the profile is output
    ``repeat_count + 1`` times, and ``REPEAT_FOREVER`` repeats indefinitely.

Module-type capability differences
    ``Controller.module_type`` reports the module family (``ModuleType``).
    Capability differences are exposed as queries: ``supports_trigger_mode``,
    ``supports_fan_control``, ``requires_initialization``, and
    ``max_profile_steps``. Requesting an unsupported operation (for example
    trigger configuration on an MA or CA module, or fan control on a module
    without a fan) raises ``UnsupportedOperationError``.

Memory persistence
    Settings are volatile until committed. ``Controller.store_settings()``
    writes the current settings of all channels and modes to non-volatile
    memory so they survive a power cycle. ``Controller.restore_factory_defaults()``
    loads factory defaults into the current settings (call ``store_settings()``
    afterward to persist them). ``Controller.soft_reset()`` performs a soft
    reset.

Read-back
    ``Channel.read_parameters()`` returns a snapshot of all mode parameters
    plus the active mode. ``Channel.get_active_mode()`` returns just the active
    mode. ``Channel.read_load_voltage()`` returns the load voltage in
    millivolts, the unit the documents state. The documents present this as a
    feature of the voltage-monitoring module variants, so it is gated behind
    ``Controller.supports_load_voltage`` and raises
    ``UnsupportedOperationError`` on modules that do not provide it. It is only
    meaningful in NORMAL mode or a slow STROBE mode because the controller polls
    the load at a 20 ms interval.

Error model
    The public API reports failure with exceptions, never return codes. The
    hierarchy is rooted at ``MightexLEDError``. ``DeviceConnectionError`` covers
    transport and handle failures, with ``DeviceNotFoundError`` as the specific
    case where a device index cannot be opened. ``DeviceCommandError`` covers an
    error the device reports while executing an accepted command, and carries
    the device error code when one is available. ``UnsupportedOperationError``
    covers operations a module does not provide, and ``ControllerClosedError``
    covers use of a closed controller. Invalid arguments raise the built-in
    ``ValueError``. The documents report a device-side error as a single
    condition and do not separate an out-of-range argument from other execution
    errors, so both surface as ``DeviceCommandError``.

Transport scope
    The public contract is transport-neutral; no USB, HID, or serial detail
    appears in any signature. This API targets the Sirius USB controller family
    (SLC-XXXX-U). RS232 controllers expose the same logical capabilities
    through a different backend and could be supported behind the same surface
    without changing the public contract.

Low-level escape hatch
    None is exposed. Every documented capability is reachable through a named
    method, including capabilities the vendor SDK reaches only by sending a raw
    command (device information, host control initialization, and fan control).
    Raw protocol strings are intentionally not part of the public API.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum
from types import TracebackType


REPEAT_FOREVER: int = 9999
"""Strobe repeat count value that repeats the profile indefinitely.

Because this value is reserved, a strobe profile cannot be asked to output
exactly 10000 times. Pass ``REPEAT_FOREVER`` for indefinite repetition instead.
"""


ProfileStep = tuple[float, int]
"""A single profile step as ``(current_ma, time_us)``.

``current_ma`` is the step current in milliamps. ``time_us`` is the step
duration as a whole number of microseconds.
"""

Profile = Sequence[ProfileStep]
"""An ordered sequence of profile steps, without the terminating zero pair."""


class OperatingMode(IntEnum):
    """Working mode of a channel.

    Each channel independently holds parameters for NORMAL, STROBE, and
    TRIGGER, and one mode is active at a time. DISABLE turns the channel output
    off.
    """

    DISABLE = 0
    NORMAL = 1
    STROBE = 2
    TRIGGER = 3


class TriggerPolarity(IntEnum):
    """External trigger edge that asserts the trigger profile."""

    RISING = 0
    FALLING = 1


class ModuleType(IntEnum):
    """Module family reported by a controller.

    The family does not always distinguish hardware variants. For example the
    SLC-MA04-MU and SLC-CA04-MU variants report as MA and CA but differ in
    behavior. Prefer the controller capability queries (``supports_trigger_mode``,
    ``supports_fan_control``, ``requires_initialization``, ``max_profile_steps``)
    over switching on this value.
    """

    AA = 0
    AV = 1
    SA = 2
    SV = 3
    MA = 4
    CA = 5
    HA = 6
    HV = 7
    FA = 8
    FV = 9
    XA = 10
    XV = 11
    QA = 12


class MightexLEDError(Exception):
    """Base class for all errors raised by this library."""


class DeviceConnectionError(MightexLEDError):
    """Raised when a controller cannot be opened or a transport-level call
    fails, including use of a device handle that is no longer valid."""


class DeviceNotFoundError(DeviceConnectionError):
    """Raised when ``open_device`` cannot open the device at the requested
    index.

    The documents report this as an open failure for that index and do not give
    a more specific cause. It is catchable as ``DeviceConnectionError``.
    """


class DeviceCommandError(MightexLEDError):
    """Raised when the controller accepts an operation but reports an error
    while executing it.

    Attributes:
        code: Device-reported error code if one is available, otherwise
            ``None``. Populated by the implementation.
    """

    code: int | None


class UnsupportedOperationError(MightexLEDError):
    """Raised when an operation is not supported by the connected module, for
    example trigger configuration on an MA or CA module, or fan control on a
    module without a fan."""


class ControllerClosedError(MightexLEDError):
    """Raised when a controller or one of its channel handles is used after the
    controller has been closed."""


@dataclass(frozen=True)
class NormalParameters:
    """NORMAL mode parameters of a channel.

    Attributes:
        current_max_ma: Maximum allowed current in milliamps.
        current_set_ma: Working current in milliamps.
    """

    current_max_ma: float
    current_set_ma: float


@dataclass(frozen=True)
class StrobeParameters:
    """STROBE mode parameters of a channel.

    Attributes:
        current_max_ma: Maximum allowed current in milliamps.
        repeat_count: Device repeat count. The profile is output
            ``repeat_count + 1`` times, or indefinitely when equal to
            ``REPEAT_FOREVER``.
        profile: Ordered ``(current_ma, time_us)`` steps, with the terminating
            zero pair removed.
    """

    current_max_ma: float
    repeat_count: int
    profile: tuple[ProfileStep, ...]


@dataclass(frozen=True)
class TriggerParameters:
    """TRIGGER mode parameters of a channel.

    Attributes:
        current_max_ma: Maximum allowed current in milliamps.
        polarity: Trigger edge that asserts the profile.
        profile: Ordered ``(current_ma, time_us)`` steps, with the terminating
            zero pair removed.
    """

    current_max_ma: float
    polarity: TriggerPolarity
    profile: tuple[ProfileStep, ...]


@dataclass(frozen=True)
class ChannelState:
    """Snapshot of a channel read back from the device.

    Attributes:
        active_mode: The mode currently driving the channel output.
        normal: Stored NORMAL mode parameters.
        strobe: Stored STROBE mode parameters.
        trigger: Stored TRIGGER mode parameters.
    """

    active_mode: OperatingMode
    normal: NormalParameters
    strobe: StrobeParameters
    trigger: TriggerParameters


@dataclass(frozen=True)
class DeviceInfo:
    """Identifying information reported by a controller.

    Attributes:
        device_type: Module or device type string.
        firmware_version: Firmware version string.
        serial_number: Serial number string.
        raw: The full information line exactly as reported by the controller.
    """

    device_type: str
    firmware_version: str
    serial_number: str
    raw: str


@dataclass(frozen=True)
class DeviceDescriptor:
    """Identity of a connected controller as seen during discovery.

    ``enumerate_devices()`` returns one of these per connected controller.

    The documents expose only the number of connected controllers before a
    controller is opened. Serial number, module type, and channel count are read
    through functions that need an open device, so they are reported here as
    ``None`` and become available from the opened ``Controller``. The
    implementation may fill them in if it can read them at discovery time;
    otherwise they remain ``None`` and are never guessed.

    Attributes:
        index: Zero-based device index passed to ``open_device()``.
        serial_number: Serial number if readable before opening, else ``None``.
        module_type: Module family if readable before opening, else ``None``.
        channel_count: Channel count if readable before opening, else ``None``.
    """

    index: int
    serial_number: str | None = None
    module_type: ModuleType | None = None
    channel_count: int | None = None


class Channel:
    """A single LED output channel of a controller.

    A channel is a live handle obtained from ``Controller.channel()`` or
    ``Controller.channels``. It is bound to one one-based channel number on its
    controller. Configuring a mode stores that mode's parameters but does not
    change the physical output until the mode is made active with
    ``set_active_mode()``. Every operation on a channel whose controller has
    been closed raises ``ControllerClosedError``.

    Channels are not created directly.
    """

    @property
    def number(self) -> int:
        """The one-based channel number of this channel on its controller."""
        ...

    def configure_normal(
        self, current_max_ma: float, current_set_ma: float
    ) -> None:
        """Store NORMAL mode parameters for this channel.

        Args:
            current_max_ma: Maximum current in milliamps. Must be non-negative.
                Rounded to the nearest device step (see
                ``Controller.current_resolution_ma``).
            current_set_ma: Working current in milliamps. Must be non-negative
                and not greater than ``current_max_ma``. Rounded to the nearest
                device step.

        This does not change the output unless NORMAL is the active mode.

        Raises:
            ValueError: If a current is negative or ``current_set_ma`` exceeds
                ``current_max_ma``.
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def set_normal_current(self, current_ma: float) -> None:
        """Set only the NORMAL mode working current, leaving the maximum
        unchanged.

        Args:
            current_ma: Working current in milliamps. Must be non-negative and
                not greater than the maximum already configured for NORMAL
                mode. Rounded to the nearest device step.

        This does not change the output unless NORMAL is the active mode.

        Raises:
            ValueError: If ``current_ma`` is negative.
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error,
                including a value above the configured maximum.
        """
        ...

    def configure_strobe(
        self,
        current_max_ma: float,
        profile: Profile,
        repeat_count: int = 0,
    ) -> None:
        """Store STROBE mode parameters for this channel.

        Args:
            current_max_ma: Maximum current in milliamps. Must be non-negative.
                Rounded to the nearest device step.
            profile: Ordered ``(current_ma, time_us)`` steps. ``current_ma`` is
                in milliamps and is rounded to the nearest device step.
                ``time_us`` is a whole number of microseconds. Do not include
                the terminating zero pair; it is added automatically. The number
                of steps must not exceed ``Controller.max_profile_steps``. An
                empty profile leaves the channel off in STROBE mode.
            repeat_count: Device repeat count from 0 to 99999999. The profile is
                output ``repeat_count + 1`` times. Pass ``REPEAT_FOREVER`` to
                repeat indefinitely. Defaults to 0, which outputs the profile
                once.

        This does not change the output unless STROBE is the active mode. When
        STROBE is already active, re-activating it with ``set_active_mode()``
        restarts the profile.

        Raises:
            ValueError: If a current is negative, if a step value is negative,
                if the profile is longer than the module allows, or if
                ``repeat_count`` is out of range.
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def configure_trigger(
        self,
        current_max_ma: float,
        profile: Profile,
        polarity: TriggerPolarity = TriggerPolarity.RISING,
    ) -> None:
        """Store TRIGGER mode parameters for this channel.

        Args:
            current_max_ma: Maximum current in milliamps. Must be non-negative.
                Rounded to the nearest device step.
            profile: Ordered ``(current_ma, time_us)`` steps, with the same
                rules as ``configure_strobe``. Do not include the terminating
                zero pair. The number of steps must not exceed
                ``Controller.max_profile_steps``.
            polarity: External trigger edge that asserts the profile. Defaults
                to rising.

        This does not change the output unless TRIGGER is the active mode. The
        stored profile runs once per external trigger while TRIGGER is active.

        Raises:
            UnsupportedOperationError: If the module does not support trigger
                mode (for example MA and CA modules).
            ValueError: If a current is negative, if a step value is negative,
                or if the profile is longer than the module allows.
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def set_active_mode(self, mode: OperatingMode) -> None:
        """Select the active working mode for this channel.

        The channel output immediately follows the stored parameters of the
        selected mode. Selecting STROBE starts the stored strobe profile, and
        selecting STROBE again while already in STROBE restarts it.

        Args:
            mode: The mode to make active.

        Raises:
            UnsupportedOperationError: If ``mode`` is TRIGGER and the module
                does not support trigger mode.
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def get_active_mode(self) -> OperatingMode:
        """Read back the mode currently driving this channel.

        Returns:
            The active ``OperatingMode``.

        Raises:
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def read_parameters(self) -> ChannelState:
        """Read back the stored parameters of all modes and the active mode.

        Currents are returned in milliamps and profiles are returned without
        the terminating zero pair.

        Returns:
            A ``ChannelState`` snapshot.

        Raises:
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def read_load_voltage(self) -> int:
        """Read the present load voltage on this channel.

        The documents present load voltage read-back as a feature of the
        voltage-monitoring module variants. The controller polls the load at a
        20 ms interval, so this reading is only meaningful in NORMAL mode or a
        slow STROBE mode.

        Returns:
            The load voltage in millivolts, the unit the device reports.

        Raises:
            UnsupportedOperationError: If the module does not provide load
                voltage read-back (see ``Controller.supports_load_voltage``).
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...


class Controller:
    """A connected Sirius USB LED controller.

    A controller owns the channels of one device and provides device-wide
    operations. Obtain channels with ``channel()`` or ``channels``. Close the
    controller with ``close()``, or use it as a context manager. After it is
    closed, the controller and all of its channels raise
    ``ControllerClosedError``.

    Controllers are created with ``open_device()``, not directly.
    """

    @property
    def serial_number(self) -> str:
        """The controller serial number."""
        ...

    @property
    def channel_count(self) -> int:
        """The number of output channels on this controller."""
        ...

    @property
    def module_type(self) -> ModuleType:
        """The module family of this controller."""
        ...

    @property
    def current_resolution_ma(self) -> float:
        """The current step size in milliamps for this module.

        The documents state 1.0 for AA, AV, SA, SV, HA, HV, MA, and CA modules,
        and 0.1 for FA, FV, XA, and XV modules. They do not state a resolution
        for QA modules, so the value returned for a QA module is determined by
        the implementation and is not a documented fact. Current values passed
        to channel methods are rounded to the nearest multiple of this step.
        """
        ...

    @property
    def max_profile_steps(self) -> int:
        """The maximum number of usable strobe or trigger profile steps for
        this module, not counting the terminating zero pair.

        The documents give 127 usable steps for modules that allow the full
        profile and as few as 2 for modules they describe as limited, without
        listing which modules fall into the limited group.
        """
        ...

    @property
    def supports_trigger_mode(self) -> bool:
        """Whether this module supports TRIGGER mode. False for MA and CA
        modules."""
        ...

    @property
    def supports_load_voltage(self) -> bool:
        """Whether this module supports load voltage read-back.

        The documents describe this read-back for the voltage-monitoring (V)
        module variants, giving AV04 and SV04 as examples. On modules without
        it, ``Channel.read_load_voltage`` raises ``UnsupportedOperationError``.
        """
        ...

    @property
    def supports_fan_control(self) -> bool:
        """Whether this module exposes fan control. True only for the
        SLC-MA04-MU and SLC-CA04-MU variants."""
        ...

    @property
    def requires_initialization(self) -> bool:
        """Whether this module must be prepared with ``initialize()`` before it
        accepts control. True only for the SLC-MA04-MU and SLC-CA04-MU
        variants."""
        ...

    @property
    def is_closed(self) -> bool:
        """Whether this controller has been closed."""
        ...

    def channel(self, number: int) -> Channel:
        """Return the channel handle for a one-based channel number.

        The returned ``Channel`` is a live handle bound to the channel, not a
        snapshot. Calling this again with the same number returns the same
        object.

        Args:
            number: One-based channel number, from 1 to ``channel_count``.

        Returns:
            The ``Channel`` for that number.

        Raises:
            ValueError: If ``number`` is outside 1 to ``channel_count``.
            ControllerClosedError: If the controller is closed.
        """
        ...

    @property
    def channels(self) -> tuple[Channel, ...]:
        """All channel handles in order from channel 1 to ``channel_count``.
        These are the same handles returned by ``channel()``."""
        ...

    def device_info(self) -> DeviceInfo:
        """Query identifying information from the controller.

        Returns:
            A ``DeviceInfo`` with the device type, firmware version, and serial
            number.

        Raises:
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def initialize(self) -> None:
        """Put the controller into host control mode.

        The documents require this for the SLC-MA04-MU and SLC-CA04-MU variants
        before any channel or device operation. For other modules the documents
        do not require it; the library treats calling it as a harmless no-op.
        Use ``requires_initialization`` to check whether the connected module
        needs it.

        Raises:
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def store_settings(self) -> None:
        """Write the current settings of all channels and modes to non-volatile
        memory so they survive a power cycle.

        Without this, settings are lost on power down and revert to the last
        stored values or to factory defaults.

        Raises:
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def restore_factory_defaults(self) -> None:
        """Load factory default settings into the current settings of all
        channels and modes.

        This changes the current settings only. Call ``store_settings()``
        afterward to persist the defaults to non-volatile memory. The factory
        defaults place every channel in DISABLE mode, with NORMAL maximum 20 mA
        and working current 10 mA, and STROBE and TRIGGER each with maximum
        20 mA and no profile points.

        Raises:
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def soft_reset(self) -> None:
        """Perform a soft reset of the controller.

        Raises:
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def set_fan_pwm_level(self, level: int) -> None:
        """Set the cooling fan drive level.

        Only the SLC-MA04-MU and SLC-CA04-MU variants provide fan control.

        Args:
            level: Fan drive level from 0 to 10, where 0 is fully off and 10 is
                fully on, in 10 percent steps.

        Raises:
            UnsupportedOperationError: If the module does not provide fan
                control.
            ValueError: If ``level`` is outside 0 to 10.
            ControllerClosedError: If the controller is closed.
            DeviceConnectionError: If the transport call fails.
            DeviceCommandError: If the controller reports an execution error.
        """
        ...

    def close(self) -> None:
        """Close the controller and release it.

        After closing, the controller and all of its channels raise
        ``ControllerClosedError``. Closing an already closed controller has no
        effect.

        Raises:
            DeviceConnectionError: If the transport call fails while closing.
        """
        ...

    def __enter__(self) -> Controller:
        """Enter a context manager and return this controller."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the controller on context exit. Does not suppress
        exceptions."""
        ...


def enumerate_devices() -> tuple[DeviceDescriptor, ...]:
    """Scan for connected Sirius USB controllers.

    Refreshes the set of known devices and returns one ``DeviceDescriptor`` per
    connected controller, in index order. The descriptor index, from 0 to the
    number of controllers minus 1, is passed to ``open_device()``. Call this
    before ``open_device()``.

    The documents expose only the number of connected controllers at this point.
    A descriptor therefore reports serial number, module type, and channel count
    as unavailable (``None``) unless the implementation can read them before the
    controller is opened. Those values are available from the opened
    ``Controller``.

    Returns:
        A tuple of ``DeviceDescriptor`` objects, empty if none are connected.
    """
    ...


def open_device(index: int) -> Controller:
    """Open a connected controller by index.

    Call ``enumerate_devices()`` first to discover connected controllers and
    their indices. The returned controller can be used directly or as a context
    manager, for example ``with open_device(0) as controller: ...``.

    Args:
        index: Zero-based device index, the ``index`` field of a
            ``DeviceDescriptor`` from ``enumerate_devices()``.

    Returns:
        An open ``Controller``.

    Raises:
        ValueError: If ``index`` is negative.
        DeviceNotFoundError: If the device at the index cannot be opened.
    """
    ...


__all__ = [
    "REPEAT_FOREVER",
    "ProfileStep",
    "Profile",
    "OperatingMode",
    "TriggerPolarity",
    "ModuleType",
    "MightexLEDError",
    "DeviceConnectionError",
    "DeviceNotFoundError",
    "DeviceCommandError",
    "UnsupportedOperationError",
    "ControllerClosedError",
    "NormalParameters",
    "StrobeParameters",
    "TriggerParameters",
    "ChannelState",
    "DeviceInfo",
    "DeviceDescriptor",
    "Channel",
    "Controller",
    "enumerate_devices",
    "open_device",
]
