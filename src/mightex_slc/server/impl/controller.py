# ------------------------------------------------------------------------------
#  Filename: controller.py
#
#  Purpose: Real device model for one controller, owned by the server.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The real device model for a controller, not a proxy.

This is the actual logic the API skeleton described: it tracks the device's modes
and parameters, enforces capability rules (for example refusing trigger
operations on modules that lack trigger mode), and issues commands through the
transport. One of these exists per open device and is owned by session.
"""
