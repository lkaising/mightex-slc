# ------------------------------------------------------------------------------
#  Filename: channel.py
#
#  Purpose: Real per-channel device model behind a controller.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The real per-channel device model, counterpart to the client's channel proxy.

It holds a channel's per-mode parameters and active mode, applies the per-module
current rounding, assembles profiles with the internal terminator, and calls the
transport to actually drive output. This is where a channel-level request finally
becomes a hardware action.
"""
