# ------------------------------------------------------------------------------
#  Filename: rs232_transport.py
#
#  Purpose: Real serial backend over pyserial, using the rs232 codec.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The real hardware backend, implementing the transport interface over pyserial.

It opens the serial port, sends commands encoded by the rs232 codec, and reads
and decodes the replies. The port is always explicit or configured: open_device
receives the serial device path, or falls back to a default bound at
construction (constructor argument, environment, or config) when one exists;
with no configured default, open_device(None) fails the open. This backend
never scans or probes ports — opening a port is side-effecting (ECHOOFF enters
PC Mode on MA/CA modules), so it opens only the one it is told to. This is the
file that touches an actual device, and it is where the single-owner-port
concern (two processes cannot share one port) will need handling if it becomes
real.
"""
