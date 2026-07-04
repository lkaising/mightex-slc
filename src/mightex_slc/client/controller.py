# ------------------------------------------------------------------------------
#  Filename: controller.py
#
#  Purpose: Client-side proxy for one open controller, identified by device_id.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The Controller proxy: the client-side stand-in for a device that lives on the
server.

A Controller holds a device_id, the handle returned when a device is opened, and
nothing else. Its methods (device info, initialize, store settings, restore
factory defaults, soft reset, fan level, close, the read-only capability
properties, and channel(n)) each build the matching device-level contract
request and send it through link. It is a typed, stateless reference to the real
device, which the server owns. Context-manager support (with open_device(...) as
ctrl) is wired here, so the controller closes itself on exit.
"""
