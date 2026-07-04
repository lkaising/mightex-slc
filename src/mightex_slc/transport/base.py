# ------------------------------------------------------------------------------
#  Filename: base.py
#
#  Purpose: The transport interface both backends satisfy; the swap seam.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The interface both backends satisfy: the swap seam.

It defines the hardware-agnostic transport contract (open, close, send a command,
read a response) that the server device model drives. Because the device model
only knows this interface, the fake and the real backend are interchangeable, and
nothing above transport knows or cares which is in use.
"""
