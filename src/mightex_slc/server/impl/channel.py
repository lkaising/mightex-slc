# ------------------------------------------------------------------------------
#  Filename: channel.py
#
#  Purpose: Real per-channel device model behind a controller.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The real per-channel device model, counterpart to the client's channel proxy.

It applies per-channel capability policy (for example refusing TRIGGER on
modules without trigger mode) and calls the transport to make a channel-level
request a hardware action. It holds no mode or parameter state and never
rescales a value: currents pass through to the transport exactly as validated
at the contract.
"""

from __future__ import annotations

from ...contract import (
    ControllerCapabilities,
    NormalParameters,
    OperatingMode,
    StepProfile,
    TriggerParameters,
    TriggerProfile,
)
from ...transport import CommandRejectedError, Transport, TransportHandle


class ChannelModel:
    """One channel of an open controller; built by ControllerModel.channel()."""

    __slots__ = ("_capabilities", "_handle", "_number", "_transport")

    def __init__(
        self,
        transport: Transport,
        handle: TransportHandle,
        capabilities: ControllerCapabilities,
        number: int,
    ) -> None:
        self._transport = transport
        self._handle = handle
        self._capabilities = capabilities
        self._number = number

    @property
    def capabilities(self) -> ControllerCapabilities:
        return self._capabilities

    @property
    def number(self) -> int:
        return self._number

    def set_normal_parameters(self, parameters: NormalParameters) -> None:
        """Store NORMAL-mode parameters for this channel; output unchanged."""
        self._transport.set_normal_parameters(self._handle, self._number, parameters)

    def get_normal_parameters(self) -> NormalParameters:
        """Read back the NORMAL-mode parameters stored for this channel."""
        return self._transport.get_normal_parameters(self._handle, self._number)

    def set_trigger_parameters(self, parameters: TriggerParameters) -> None:
        """Store TRIGGER-mode parameters for this channel; output unchanged."""
        self._require_trigger_support("TRIGGER-mode configuration")
        self._transport.set_trigger_parameters(self._handle, self._number, parameters)

    def get_trigger_parameters(self) -> TriggerParameters:
        """Read back the TRIGGER-mode parameters stored for this channel."""
        self._require_trigger_support("TRIGGER-mode configuration")
        return self._transport.get_trigger_parameters(self._handle, self._number)

    def set_trigger_profile(self, profile: TriggerProfile) -> None:
        """Store a trigger profile for this channel; output unchanged."""
        self._require_trigger_support("TRIGGER-mode configuration")
        limit = self._capabilities.max_profile_steps
        if isinstance(profile, StepProfile) and len(profile.steps) > limit:
            family = self._capabilities.module_type.name
            raise CommandRejectedError(
                f"profile has {len(profile.steps)} steps; {family} modules store at most {limit}"
            )
        self._transport.set_trigger_profile(self._handle, self._number, profile)

    def get_trigger_profile(self) -> TriggerProfile:
        """Read back the trigger profile stored for this channel."""
        self._require_trigger_support("TRIGGER-mode configuration")
        return self._transport.get_trigger_profile(self._handle, self._number)

    def set_active_mode(self, mode: OperatingMode) -> None:
        """Make a mode active on this channel, effective immediately."""
        if mode is OperatingMode.TRIGGER:
            self._require_trigger_support("TRIGGER mode")
        self._transport.set_active_mode(self._handle, self._number, mode)

    def get_active_mode(self) -> OperatingMode:
        """Read back the mode currently driving this channel."""
        return self._transport.get_active_mode(self._handle, self._number)

    def _require_trigger_support(self, subject: str) -> None:
        if not self._capabilities.supports_trigger_mode:
            family = self._capabilities.module_type.name
            raise CommandRejectedError(f"{subject} is not available on {family} modules")

    def __repr__(self) -> str:
        module = self._capabilities.module_type.name
        return f"<{type(self).__name__} number={self._number} module={module}>"
