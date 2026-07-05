# ------------------------------------------------------------------------------
#  Filename: module_type.py
#
#  Purpose: Define controller module families using device integer codes.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from enum import IntEnum


class ModuleType(IntEnum):
    """Module family reported by a controller.

    The integer ordering is non-alphabetical and load-bearing; it is the
    device's own numbering and must never be renumbered. The family does not
    always distinguish hardware variants (for example SLC-MA04-MU and
    SLC-CA04-MU report as MA and CA but differ in behavior), so prefer the
    controller capabilities over switching on this value.
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
