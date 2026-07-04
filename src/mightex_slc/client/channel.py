# ------------------------------------------------------------------------------
#  Filename: channel.py
#
#  Purpose: Client-side proxy for one channel, bound to a device_id and number.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The Channel proxy: a typed, bound reference to one channel of an open device.

A Channel holds a device_id plus a one-based channel number and is obtained from
controller.channel(n). Its methods (configure normal, strobe, and trigger, set
normal current, set and get active mode, read parameters, and read load voltage)
each map to a per-channel contract operation. Like the Controller proxy, it holds
no device state; it is a way to name one channel when building requests, which
are sent through link.
"""
