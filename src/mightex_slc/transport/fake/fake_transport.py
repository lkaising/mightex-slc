# ------------------------------------------------------------------------------
#  Filename: fake_transport.py
#
#  Purpose: Pure-Python simulated device implementing the transport interface.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
A pure-Python simulated controller implementing the transport interface.

It responds the way a device would, with no hardware attached. This is what the
acceptance example runs against, and what lets the client, server, and contract
be exercised end to end before any real controller is connected.

The device simulated is chosen by a persona: MA04_PERSONA (the default, and
what open_fake_device() uses — no trigger mode, which keeps the no-trigger
capability path exercised) or SA04_PERSONA (trigger-capable, mirroring the
bench unit, for exercising the trigger configuration path).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from ...contract import (
    ControllerCapabilities,
    FollowerProfile,
    ModuleType,
    NormalParameters,
    OperatingMode,
    ProfileStep,
    StepProfile,
    TriggerParameters,
    TriggerPolarity,
    TriggerProfile,
)
from ..base import (
    CommandRejectedError,
    InvalidHandleError,
    Transport,
    TransportError,
    TransportHandle,
    TransportOpenResult,
)


@dataclass(frozen=True, slots=True)
class FakePersona:
    """One simulated controller variant: identity, capabilities, and ceilings.

    The ceilings are the vendor module-matrix values the fake enforces or
    clamps against; they are device limits, not capabilities the contract
    reports.
    """

    serial_number: str
    capabilities: ControllerCapabilities
    normal_ceiling_ma: float
    pulsed_ceiling_ma: float


# Serial numbers mimic the vendor's observed 04-XXXXXX-NNN shape with
# deliberately synthetic digits — a library convention, not a device fact.

# One simulated SLC-MA04-MU. Every value below is a documented fact for that
# variant (protocol.md §§5-8): no TRIGGER mode, and the pulsed ceiling equals
# the NORMAL ceiling (1200 mA on the -MU variant). PC-Mode entry via ECHOOFF
# is folded into open_device, so no capability needs to instruct the caller
# about it.
MA04_PERSONA = FakePersona(
    serial_number="04-000000-001",
    capabilities=ControllerCapabilities(
        module_type=ModuleType.MA,
        channel_count=4,
        current_resolution_ma=1.0,
        max_profile_steps=2,
        supports_trigger_mode=False,
        supports_load_voltage=False,
        supports_fan_control=True,
    ),
    normal_ceiling_ma=1200.0,
    pulsed_ceiling_ma=1200.0,
)

# One simulated SLC-SA04, mirroring the bench unit: trigger-capable, NORMAL
# ceiling 1000 mA, pulsed ceiling 3500 mA (protocol.md §7, bench-confirmed).
SA04_PERSONA = FakePersona(
    serial_number="04-000000-002",
    capabilities=ControllerCapabilities(
        module_type=ModuleType.SA,
        channel_count=4,
        current_resolution_ma=1.0,
        max_profile_steps=2,
        supports_trigger_mode=True,
        supports_load_voltage=False,
        supports_fan_control=False,
    ),
    normal_ceiling_ma=1000.0,
    pulsed_ceiling_ma=3500.0,
)

# The measured factory trigger profile: one (10 mA, 20 µs) step. The vendor
# documents "empty", but the bench read this back on every channel after
# RESTOREDEF (protocol.md §6, 2026-07-12).
_FACTORY_TRIGGER_PROFILE = StepProfile(steps=(ProfileStep(current_ma=10.0, duration_us=20),))


@dataclass(slots=True)
class FakeChannelState:
    """One channel's live state, starting at the factory defaults.

    NORMAL defaults are the vendor-documented safety floor (Imax 20 mA /
    Iset 10 mA); the trigger defaults are the bench-measured ones — Imax
    10 mA, rising polarity, one (10 mA, 20 µs) step — which contradict the
    vendor's documented 20 mA / empty profile (protocol.md §6).
    """

    active_mode: OperatingMode = OperatingMode.DISABLE
    normal_current_max_ma: float = 20.0
    normal_current_set_ma: float = 10.0
    trigger_current_max_ma: float = 10.0
    trigger_polarity: TriggerPolarity = TriggerPolarity.RISING
    trigger_profile: StepProfile | FollowerProfile = field(
        default_factory=lambda: _FACTORY_TRIGGER_PROFILE
    )


class FakeTransport(Transport):
    """A single in-memory controller, simulated per the chosen persona.

    Channel state persists across close — a real controller keeps driving its
    outputs when the serial port closes, so closing is never a safety action
    and the end state stays inspectable afterwards.
    """

    def __init__(self, persona: FakePersona = MA04_PERSONA) -> None:
        self._persona = persona
        count = persona.capabilities.channel_count
        self._channels = [FakeChannelState() for _ in range(count)]
        self._open_handle: TransportHandle | None = None

    def open_device(self, port: str | None = None) -> TransportOpenResult:
        # port is accepted for interface compatibility and deliberately inert:
        # the fake is the device at whatever target the caller imagines, so
        # None is fine. It does not model host serial-port availability, and
        # opening with a path never proves that path exists.
        if self._open_handle is not None:
            raise TransportError("device is already open")
        self._open_handle = TransportHandle()
        return TransportOpenResult(
            handle=self._open_handle,
            serial_number=self._persona.serial_number,
            capabilities=self._persona.capabilities,
        )

    def set_normal_parameters(
        self,
        handle: TransportHandle,
        channel: int,
        parameters: NormalParameters,
    ) -> None:
        self._require_open(handle)
        state = self._channel(channel)
        self._require_current_in_range("current_max_ma", parameters.current_max_ma)
        self._require_current_in_range("current_set_ma", parameters.current_set_ma)
        # Stores parameters only; output changes only via set_active_mode.
        # set > max cannot arrive here: NormalParameters refuses it at
        # construction, so the real device's behavior there stays an open
        # question this fake never has to answer.
        state.normal_current_max_ma = parameters.current_max_ma
        state.normal_current_set_ma = parameters.current_set_ma

    def get_normal_parameters(self, handle: TransportHandle, channel: int) -> NormalParameters:
        self._require_open(handle)
        state = self._channel(channel)
        return NormalParameters(
            current_max_ma=state.normal_current_max_ma,
            current_set_ma=state.normal_current_set_ma,
        )

    def set_trigger_parameters(
        self,
        handle: TransportHandle,
        channel: int,
        parameters: TriggerParameters,
    ) -> None:
        self._require_open(handle)
        state = self._channel(channel)
        self._require_trigger_capable()
        # The real device never rejects trigger arguments: a current limit
        # above the pulsed ceiling is silently clamped to it while still
        # acknowledging (bench-measured, protocol.md quirk #15). Modeling the
        # clamp keeps the verify-by-read-back story honest without hardware.
        clamped = min(parameters.current_max_ma, self._persona.pulsed_ceiling_ma)
        state.trigger_current_max_ma = clamped
        state.trigger_polarity = parameters.polarity

    def get_trigger_parameters(self, handle: TransportHandle, channel: int) -> TriggerParameters:
        self._require_open(handle)
        state = self._channel(channel)
        self._require_trigger_capable()
        return TriggerParameters(
            current_max_ma=state.trigger_current_max_ma,
            polarity=state.trigger_polarity,
        )

    def set_trigger_profile(
        self,
        handle: TransportHandle,
        channel: int,
        profile: TriggerProfile,
    ) -> None:
        self._require_open(handle)
        state = self._channel(channel)
        self._require_trigger_capable()
        # Step currents clamp against the trigger current limit stored right
        # now, mirroring the device's write-time clamp (protocol.md quirk
        # #15). A later limit change does not retroactively re-clamp — the
        # real device's behavior there is unknown, so the fake leaves stored
        # profiles alone.
        limit = state.trigger_current_max_ma
        if isinstance(profile, FollowerProfile):
            state.trigger_profile = FollowerProfile(current_ma=min(profile.current_ma, limit))
        else:
            state.trigger_profile = StepProfile(
                steps=tuple(
                    ProfileStep(
                        current_ma=min(step.current_ma, limit),
                        duration_us=step.duration_us,
                    )
                    for step in profile.steps
                )
            )

    def get_trigger_profile(self, handle: TransportHandle, channel: int) -> TriggerProfile:
        self._require_open(handle)
        state = self._channel(channel)
        self._require_trigger_capable()
        return state.trigger_profile

    def set_active_mode(self, handle: TransportHandle, channel: int, mode: OperatingMode) -> None:
        self._require_open(handle)
        state = self._channel(channel)
        if mode is OperatingMode.TRIGGER and not self._supports_trigger:
            # TRIGGER is absent on MA modules. The exact wire response is
            # unverified, so the refusal surfaces as a rejected command.
            family = self._persona.capabilities.module_type.name
            raise CommandRejectedError(f"TRIGGER mode is not available on {family} modules")
        state.active_mode = mode  # changes output, like restore_factory_defaults

    def get_active_mode(self, handle: TransportHandle, channel: int) -> OperatingMode:
        self._require_open(handle)
        return self._channel(channel).active_mode

    def persist_settings(self, handle: TransportHandle) -> None:
        self._require_open(handle)
        # The fake never models a power cycle, so persisted state would be
        # unobservable; acknowledging without effect is the honest simulation.

    def restore_factory_defaults(self, handle: TransportHandle) -> None:
        self._require_open(handle)
        # Volatile settings only, like the device: every channel back to the
        # factory defaults, trigger state included. This changes output
        # (active channels go to DISABLE); nothing is persisted.
        count = self._persona.capabilities.channel_count
        self._channels = [FakeChannelState() for _ in range(count)]

    def close_device(self, handle: TransportHandle) -> None:
        # Idempotent by identity: only the currently open handle closes the
        # session; a stale handle is a no-op and never touches a newer one.
        if handle is self._open_handle:
            self._open_handle = None

    # The helpers below are fake-only and deliberately kept out of the
    # Transport interface; acceptance checks read the device's end state here.

    @property
    def is_open(self) -> bool:
        """Whether a handle is currently open on the fake device."""
        return self._open_handle is not None

    def channel_state(self, channel: int) -> FakeChannelState:
        """A copy of one channel's state, readable open or closed."""
        return replace(self._channel(channel))

    @property
    def _supports_trigger(self) -> bool:
        return self._persona.capabilities.supports_trigger_mode

    def _require_open(self, handle: TransportHandle) -> None:
        if self._open_handle is None or handle is not self._open_handle:
            raise InvalidHandleError("handle is not open")

    def _require_trigger_capable(self) -> None:
        if not self._supports_trigger:
            # What a real no-trigger module answers to TRIGGER/TRIGP has
            # never been captured, so the refusal surfaces as a rejected
            # command — defense behind the server's own capability guard.
            family = self._persona.capabilities.module_type.name
            raise CommandRejectedError(
                f"trigger configuration is not available on {family} modules"
            )

    def _channel(self, channel: int) -> FakeChannelState:
        count = self._persona.capabilities.channel_count
        if not 1 <= channel <= count:
            raise CommandRejectedError(f"channel {channel} out of range 1..{count}")
        return self._channels[channel - 1]

    def _require_current_in_range(self, name: str, value: float) -> None:
        ceiling = self._persona.normal_ceiling_ma
        if not 0 <= value <= ceiling:
            raise CommandRejectedError(f"{name} {value} outside 0..{ceiling} mA")
