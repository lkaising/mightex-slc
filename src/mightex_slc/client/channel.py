# ------------------------------------------------------------------------------
#  Filename: channel.py
#
#  Purpose: Client-side proxy for one channel of an open controller.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The Channel proxy: a typed, bound reference to one channel of an open device.

A Channel carries the executor and device_id of the Controller that built it,
plus a one-based channel number, and is obtained from controller.channel(n).
Its methods each map to a per-channel contract operation; this slice carries
set_normal_parameters, set_active_mode, and get_active_mode, and later slices
add the rest. Like the Controller proxy, it holds no device state and no
reference back to its Controller; it is a way to name one channel when
building requests, which are sent through link. Bad arguments raise plain
ValueError when link constructs the request model; the NormalParameters
argument to set_normal_parameters validates itself at construction, before
the call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import link

if TYPE_CHECKING:
    from .types import NormalParameters, OperatingMode


class Channel:
    """One channel of an open controller, addressed by its 1-based channel number."""

    __slots__ = ("_device_id", "_executor", "_number")

    def __init__(self, executor: link.RequestExecutor, device_id: str, number: int) -> None:
        self._executor = executor
        self._device_id = device_id
        self._number = number

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def number(self) -> int:
        return self._number

    def set_normal_parameters(self, parameters: NormalParameters) -> None:
        """Store NORMAL-mode current parameters for this channel; output is unchanged.

        Args:
            parameters: The `NormalParameters` pair to store. Constructing it
                enforces that both currents are >= 0 and that `current_set_ma`
                is no greater than `current_max_ma`.

        Raises:
            DeviceCommandError: If the device rejects the values or the
                channel `number` is out of range for the module.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        link.set_normal_parameters(self._executor, self._device_id, self._number, parameters)

    def set_active_mode(self, mode: OperatingMode) -> None:
        """Switch this channel's active working mode, effective immediately.

        Args:
            mode: The `OperatingMode` to make active: `DISABLE`, `NORMAL`,
                `STROBE`, or `TRIGGER`.

        Raises:
            ValueError: If `mode` is not a valid `OperatingMode`.
            DeviceCommandError: If the channel `number` is out of range for
                the module or the module does not support the requested mode.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        link.set_active_mode(self._executor, self._device_id, self._number, mode)

    def get_active_mode(self) -> OperatingMode:
        """Read back the mode currently driving this channel.

        Returns:
            The `OperatingMode` the channel is currently in: `DISABLE`,
            `NORMAL`, `STROBE`, or `TRIGGER`.

        Raises:
            DeviceCommandError: If the channel `number` is out of range for
                the module.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        return link.get_active_mode(self._executor, self._device_id, self._number)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} device_id={self._device_id!r} number={self._number}>"
