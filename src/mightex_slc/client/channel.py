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
configure_normal and set_active_mode, and later slices add the rest. Like the
Controller proxy, it holds no device state and no reference back to its
Controller; it is a way to name one channel when building requests, which are
sent through link. Bad arguments raise plain ValueError when link constructs
the request model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import link

if TYPE_CHECKING:
    from .types import OperatingMode


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

    def configure_normal(self, current_max_ma: float, current_set_ma: float) -> None:
        """Store NORMAL-mode current parameters for this channel; output is unchanged.

        Args:
            current_max_ma: NORMAL-mode current limit, in mA. Must be >= 0.
            current_set_ma: NORMAL-mode set current, in mA. Must be >= 0 and
                no greater than `current_max_ma`.

        Raises:
            ValueError: If either current is negative or `current_set_ma`
                exceeds `current_max_ma`.
            DeviceCommandError: If the device rejects the values or the
                channel `number` is out of range for the module.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        link.configure_normal(
            self._executor,
            self._device_id,
            self._number,
            current_max_ma=current_max_ma,
            current_set_ma=current_set_ma,
        )

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

    def __repr__(self) -> str:
        return f"<{type(self).__name__} device_id={self._device_id!r} number={self._number}>"
