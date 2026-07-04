# ------------------------------------------------------------------------------
#  Filename: session.py
#
#  Purpose: Owns the live Controller objects, keyed by device_id.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The registry that owns the live Controller objects, keyed by device_id.

This is where actual device state lives, the state the client only ever
references by id. Opening a device creates a controller here and hands back its
id; closing one disposes it; every other operation looks up its controller here
first. It is the lifecycle and ownership manager for open devices.
"""
