# ------------------------------------------------------------------------------
#  Filename: types.py
#
#  Purpose: Re-exports contract enums and models for users to import.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
A thin re-export layer over the contract package.

This module aliases the enums and shape models straight from
mightex_slc.contract, so users import them from the client without the client
ever hand-copying them. This is what keeps the contract as the single source of
truth: the client borrows the types rather than mirroring them. The current
slice surfaces the operating mode, the module type, and the controller
capabilities; later slices widen the list as their operations land.
"""

from ..contract import ControllerCapabilities, ModuleType, OperatingMode

__all__ = [
    "ControllerCapabilities",
    "ModuleType",
    "OperatingMode",
]
