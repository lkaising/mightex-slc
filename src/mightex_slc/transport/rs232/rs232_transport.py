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
and decodes the replies. This is the file that touches an actual device, and it
is where the single-owner-port concern (two processes cannot share one port) will
need handling if it becomes real.
"""
