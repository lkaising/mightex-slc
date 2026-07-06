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
    """Controller module family reported by the device.

    Values are vendor wire codes and must not be renumbered. Some hardware
    variants share a family code, so use ControllerCapabilities for behavior.
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
