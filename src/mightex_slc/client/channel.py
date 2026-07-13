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
Its methods each map to a per-channel contract operation: the NORMAL-mode
pair (set/get_normal_parameters), the TRIGGER-mode configuration pairs
(set/get_trigger_parameters, set/get_trigger_profile), and the mode pair
(set/get_active_mode); later slices add the rest. Like the Controller proxy,
it holds no device state and no reference back to its Controller; it is a way
to name one channel when building requests, which are sent through link. Bad
arguments raise plain ValueError when link constructs the request model; the
parameter and profile models validate themselves at construction, before the
call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import link

if TYPE_CHECKING:
    from .types import (
        FollowerProfile,
        NormalParameters,
        OperatingMode,
        StepProfile,
        TriggerParameters,
    )


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

    def get_normal_parameters(self) -> NormalParameters:
        """Read back the NORMAL-mode current parameters stored for this channel.

        Returns:
            The stored `NormalParameters` pair: `current_max_ma` and
            `current_set_ma`, both in mA.

        Raises:
            DeviceCommandError: If the channel `number` is out of range for
                the module.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        return link.get_normal_parameters(self._executor, self._device_id, self._number)

    def set_trigger_parameters(self, parameters: TriggerParameters) -> None:
        """Store TRIGGER-mode parameters for this channel; output is unchanged.

        Configuration only: nothing plays until TRIGGER mode is armed with
        `set_active_mode(OperatingMode.TRIGGER)`. Write the parameters before
        the profile — the device clamps profile step currents against the
        limit stored at profile-write time. The device acknowledges even when
        it silently clamps an over-ceiling limit, so verify with
        `get_trigger_parameters()` when it matters. Disable the channel
        before reprogramming an armed one.

        Args:
            parameters: The `TriggerParameters` pair to store. Constructing
                it enforces a nonnegative current limit and a valid
                `TriggerPolarity`.

        Raises:
            DeviceCommandError: If the module has no TRIGGER mode, the
                device rejects the values, or the channel `number` is out of
                range for the module.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        link.set_trigger_parameters(self._executor, self._device_id, self._number, parameters)

    def get_trigger_parameters(self) -> TriggerParameters:
        """Read back the TRIGGER-mode parameters stored for this channel.

        Returns:
            The stored `TriggerParameters`: `current_max_ma` in mA and the
            trigger `polarity`.

        Raises:
            DeviceCommandError: If the module has no TRIGGER mode or the
                channel `number` is out of range for the module.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        return link.get_trigger_parameters(self._executor, self._device_id, self._number)

    def set_trigger_profile(self, profile: StepProfile | FollowerProfile) -> None:
        """Store a trigger profile for this channel; output is unchanged.

        Configuration only: nothing plays until TRIGGER mode is armed with
        `set_active_mode(OperatingMode.TRIGGER)`. Step currents above the
        stored TRIGGER current limit are silently clamped by the device at
        write time — set the parameters first, and verify with
        `get_trigger_profile()` when it matters. A profile is written as one
        wire command per step; if a write fails partway the stored profile
        is partial and needs a complete rewrite (there is no rollback).
        Disable the channel before reprogramming an armed one.

        Args:
            profile: A `StepProfile` of timed steps (empty clears the
                profile), or a `FollowerProfile` to make the output follow
                the trigger input level.

        Raises:
            DeviceCommandError: If the module has no TRIGGER mode, the
                profile has more steps than the module stores, the device
                rejects the values, or the channel `number` is out of range
                for the module.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        link.set_trigger_profile(self._executor, self._device_id, self._number, profile)

    def get_trigger_profile(self) -> StepProfile | FollowerProfile:
        """Read back the trigger profile stored for this channel.

        Returns:
            The stored profile: a `StepProfile` (empty when the profile is
            cleared) or a `FollowerProfile`.

        Raises:
            DeviceCommandError: If the module has no TRIGGER mode or the
                channel `number` is out of range for the module.
            ControllerClosedError: If the `Controller` has been closed.
            DeviceConnectionError: If communication with the device fails.
        """
        return link.get_trigger_profile(self._executor, self._device_id, self._number)

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
