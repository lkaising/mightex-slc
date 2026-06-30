"""Device enumerations carried across the contract.

These are IntEnum because each member carries the device's own integer value.
The integer values are device facts copied exactly from the public API skeleton
and must not be reordered or renumbered.
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


class TriggerPolarity(IntEnum):
    """External trigger edge that asserts the trigger profile."""

    RISING = 0
    FALLING = 1


class ModuleType(IntEnum):
    """Module family reported by a controller.

    The integer ordering is non-alphabetical and load-bearing; it is the device's
    own numbering. The family does not always distinguish hardware variants (for
    example SLC-MA04-MU and SLC-CA04-MU report as MA and CA but differ in
    behavior), so prefer the controller capability queries over switching on this
    value.
    """

    AA = 0
    AV = 1
    SA = 2
    SV = 3
    MA = 4
    CA = 5
    HA = 6
    HV = 7
    FA = 8
    FV = 9
    XA = 10
    XV = 11
    QA = 12
