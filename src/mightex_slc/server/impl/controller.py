# ------------------------------------------------------------------------------
#  Filename: controller.py
#
#  Purpose: Real device model for one controller, owned by the server.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The real device model for a controller, not a proxy.

It owns the open transport handle and the capabilities reported at open,
enforces capability policy (for example refusing channels the module does not
have), and issues commands through the transport. It deliberately holds no
mode or parameter state: the device owns its state, and no operation in this
slice reads any back. One of these exists per open device and is owned by
session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...transport import CommandRejectedError, Transport, TransportHandle
from .channel import ChannelModel

if TYPE_CHECKING:
    from ...contract import ControllerCapabilities


class ControllerModel:
    """One open controller: handle, capabilities, and capability policy."""

    def __init__(
        self,
        transport: Transport,
        handle: TransportHandle,
        serial_number: str,
        capabilities: ControllerCapabilities,
    ) -> None:
        self._transport = transport
        self._handle = handle
        self._serial_number = serial_number
        self._capabilities = capabilities

    @classmethod
    def open(cls, transport: Transport, port: str | None = None) -> ControllerModel:
        """Open the device on a transport and wrap the result in a model."""
        result = transport.open_device(port=port)
        return cls(
            transport=transport,
            handle=result.handle,
            serial_number=result.serial_number,
            capabilities=result.capabilities,
        )

    @property
    def serial_number(self) -> str:
        """The device serial number reported at open."""
        return self._serial_number

    @property
    def capabilities(self) -> ControllerCapabilities:
        """The capability set reported at open."""
        return self._capabilities

    def channel(self, number: int) -> ChannelModel:
        """The channel model for a one-based channel number.

        The range check is capability policy, enforced here so every backend
        behaves identically; transports keep their own device truth below.
        """
        count = self._capabilities.channel_count
        if not 1 <= number <= count:
            raise CommandRejectedError(f"channel {number} out of range 1..{count}")
        return ChannelModel(
            transport=self._transport,
            handle=self._handle,
            capabilities=self._capabilities,
            number=number,
        )

    def close(self) -> None:
        """Release the device handle; idempotent through the transport."""
        self._transport.close_device(self._handle)
