# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The transport package: swappable backends behind one interface.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The transport package: the swappable bottom layer of the stack.

It exposes one interface that the device model drives, with two implementations
behind it: a pure-Python fake and the real serial path. This is what lets the
whole stack be built and run with no hardware, then pointed at a real
controller by changing one line. Beyond marking the package, this module is the
natural home for a small factory that returns the chosen backend, so the server
asks for a transport without hard-coding which one.
"""
