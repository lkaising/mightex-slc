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
    """Channel operating mode.

    Values are vendor wire codes and must not be renumbered. Mode availability
    is module-dependent; for example, MA and CA do not support TRIGGER.
    """

    DISABLE = 0
    NORMAL = 1
    STROBE = 2
    TRIGGER = 3
