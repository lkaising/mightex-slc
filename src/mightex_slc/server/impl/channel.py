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

from ...contract import ControllerCapabilities, OperatingMode
from ...transport import CommandRejectedError, Transport, TransportHandle


class ChannelModel:
    """One channel of an open controller; built by ControllerModel.channel()."""

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

    def configure_normal(
        self, current_max_ma: float, current_set_ma: float
    ) -> None:
        """Store NORMAL-mode parameters for this channel; output unchanged."""
        self._transport.configure_normal(
            self._handle, self._number, current_max_ma, current_set_ma
        )

    def set_active_mode(self, mode: OperatingMode) -> None:
        """Make a mode active on this channel, effective immediately."""
        if (
            mode is OperatingMode.TRIGGER
            and not self._capabilities.supports_trigger_mode
        ):
            family = self._capabilities.module_type.name
            raise CommandRejectedError(
                f"TRIGGER mode is not available on {family} modules"
            )
        self._transport.set_active_mode(self._handle, self._number, mode)
