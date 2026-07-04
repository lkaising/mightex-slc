# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The real device model package (controller and channel).
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The impl package: the real device model, not proxies.

These are the actual controller and channel objects that hold device state,
enforce capability rules, and drive the transport. The server's session owns them
by device_id, and dispatch calls their methods to carry out each operation.
"""
