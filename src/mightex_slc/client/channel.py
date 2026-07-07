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

from . import link
from .types import OperatingMode


class Channel:
    """One channel of an open controller, addressed by its one-based number."""

    def __init__(self, executor: link.RequestExecutor, device_id: str, number: int) -> None:
        self._executor = executor
        self._device_id = device_id
        self._number = number

    @property
    def number(self) -> int:
        """The one-based channel number this proxy addresses."""
        return self._number

    def configure_normal(self, current_max_ma: float, current_set_ma: float) -> None:
        """Store NORMAL-mode current parameters for this channel; output unchanged."""
        link.configure_normal(
            self._executor,
            self._device_id,
            self._number,
            current_max_ma=current_max_ma,
            current_set_ma=current_set_ma,
        )

    def set_active_mode(self, mode: OperatingMode) -> None:
        """Switch this channel's active working mode, effective immediately."""
        link.set_active_mode(self._executor, self._device_id, self._number, mode)
