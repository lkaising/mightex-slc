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
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from ...contract import (
    ControllerCapabilities,
    ModuleType,
    OperatingMode,
)
from ..base import (
    CommandRejectedError,
    InvalidHandleError,
    Transport,
    TransportError,
    TransportHandle,
    TransportOpenResult,
)

# The serial number mimics the vendor's observed 04-XXXXXX-NNN shape with
# deliberately synthetic digits — a library convention, not a device fact.
FAKE_SERIAL_NUMBER = "04-000000-001"

# One simulated SLC-MA04-MU. Every value below is a documented fact for that
# variant (device_and_protocol.md §§5-8). PC-Mode entry via ECHOOFF is folded
# into open_device, so no capability needs to instruct the caller about it.
FAKE_CAPABILITIES = ControllerCapabilities(
    module_type=ModuleType.MA,
    channel_count=4,
    current_resolution_ma=1.0,
    max_profile_steps=2,
    supports_trigger_mode=False,
    supports_load_voltage=False,
    supports_fan_control=True,
)

# MA04-MU current ceiling in NORMAL and STROBE (device_and_protocol.md §8).
_CURRENT_CEILING_MA = 1200.0


@dataclass(slots=True)
class FakeChannelState:
    """One channel's live state, starting at the documented factory defaults:
    DISABLE, NORMAL Imax 20 mA / Iset 10 mA (the vendor's safety floor)."""

    active_mode: OperatingMode = OperatingMode.DISABLE
    normal_current_max_ma: float = 20.0
    normal_current_set_ma: float = 10.0


class FakeTransport(Transport):
    """A single in-memory SLC-MA04-MU.

    Channel state persists across close — a real controller keeps driving its
    outputs when the serial port closes, so closing is never a safety action
    and the end state stays inspectable afterwards.
    """

    def __init__(self) -> None:
        self._channels = [
            FakeChannelState() for _ in range(FAKE_CAPABILITIES.channel_count)
        ]
        self._open_handle: TransportHandle | None = None

    def open_device(self, port: str | None = None) -> TransportOpenResult:
        # port is accepted for interface compatibility and deliberately inert:
        # the fake is the device at whichever port the caller targets (or the
        # backend default when None). It does not model host serial-port
        # availability, so opening with a path never proves that path exists.
        if self._open_handle is not None:
            raise TransportError("device is already open")
        self._open_handle = TransportHandle()
        return TransportOpenResult(
            handle=self._open_handle,
            serial_number=FAKE_SERIAL_NUMBER,
            capabilities=FAKE_CAPABILITIES,
        )

    def configure_normal(
        self,
        handle: TransportHandle,
        channel: int,
        current_max_ma: float,
        current_set_ma: float,
    ) -> None:
        self._require_open(handle)
        state = self._channel(channel)
        self._require_current_in_range("current_max_ma", current_max_ma)
        self._require_current_in_range("current_set_ma", current_set_ma)
        # Stores parameters only; output changes only via set_active_mode.
        # set > max is deliberately not checked: the real device's behavior
        # there is an open question, and the contract rejects it upstream.
        state.normal_current_max_ma = current_max_ma
        state.normal_current_set_ma = current_set_ma

    def set_active_mode(
        self, handle: TransportHandle, channel: int, mode: OperatingMode
    ) -> None:
        self._require_open(handle)
        state = self._channel(channel)
        trigger_unsupported = not FAKE_CAPABILITIES.supports_trigger_mode
        if mode is OperatingMode.TRIGGER and trigger_unsupported:
            # TRIGGER is absent on MA modules. The exact wire response is
            # unverified, so the refusal surfaces as a rejected command.
            raise CommandRejectedError("TRIGGER mode is not available on MA modules")
        state.active_mode = mode  # the only mutation that changes output

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

    def _require_open(self, handle: TransportHandle) -> None:
        if self._open_handle is None or handle is not self._open_handle:
            raise InvalidHandleError("handle is not open")

    def _channel(self, channel: int) -> FakeChannelState:
        count = FAKE_CAPABILITIES.channel_count
        if not 1 <= channel <= count:
            raise CommandRejectedError(f"channel {channel} out of range 1..{count}")
        return self._channels[channel - 1]

    def _require_current_in_range(self, name: str, value: float) -> None:
        if not 0 <= value <= _CURRENT_CEILING_MA:
            raise CommandRejectedError(
                f"{name} {value} outside 0..{_CURRENT_CEILING_MA} mA"
            )
