# ------------------------------------------------------------------------------
#  Filename: types.py
#
#  Purpose: Re-exports contract enums and models for users to import.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
A thin re-export layer over the contract package.

This module aliases the enums and shape models (operating mode, trigger polarity,
module type, channel state, device info, profile, and the rest) straight from
mightex_slc.contract, so users import them from the client without the client
ever hand-copying them. This is what keeps the contract as the single source of
truth: the client borrows the types rather than mirroring them.
"""
