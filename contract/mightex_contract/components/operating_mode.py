"""OperatingMode: the working mode of a channel.

IntEnum because each member carries the device's own integer value. The integer
values are device facts copied exactly from the public API skeleton and must not
be reordered or renumbered.
"""

from __future__ import annotations

from enum import IntEnum


class OperatingMode(IntEnum):
    """Working mode of a channel.

    Each channel independently holds parameters for NORMAL, STROBE, and TRIGGER,
    and one mode is active at a time. DISABLE turns the channel output off.
    """

    DISABLE = 0
    NORMAL = 1
    STROBE = 2
    TRIGGER = 3
