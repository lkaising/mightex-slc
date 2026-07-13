# ------------------------------------------------------------------------------
#  Filename: trigger_polarity.py
#
#  Purpose: Define trigger input edge polarity using device integer codes.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from enum import IntEnum


class TriggerPolarity(IntEnum):
    """Trigger input edge that starts profile playback.

    Values are vendor wire codes and must not be renumbered. The device
    stores any polarity byte verbatim without validating it, so this enum is
    the only guard between a typo and meaningless state on the device.
    """

    RISING = 0
    FALLING = 1
