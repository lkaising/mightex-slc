# ------------------------------------------------------------------------------
#  Filename: operating_mode.py
#
#  Purpose: Define channel operating modes using device integer codes.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from enum import IntEnum


class OperatingMode(IntEnum):
    """Working mode of a channel.

    Each channel independently holds parameters for NORMAL, STROBE, and
    TRIGGER, and one mode is active at a time. DISABLE turns the channel
    output off. The integer values are the device's own wire codes and must
    never be renumbered.
    """

    DISABLE = 0
    NORMAL = 1
    STROBE = 2
    TRIGGER = 3
