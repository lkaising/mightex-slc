"""TriggerPolarity: the external trigger edge that asserts the trigger profile.

IntEnum because each member carries the device's own integer value. The integer
values are device facts copied exactly from the public API skeleton and must not
be reordered or renumbered.
"""

from __future__ import annotations

from enum import IntEnum


class TriggerPolarity(IntEnum):
    """External trigger edge that asserts the trigger profile."""

    RISING = 0
    FALLING = 1
