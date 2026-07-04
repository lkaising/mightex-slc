# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The rs232 backend package; the private wire format lives here.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The rs232 backend package: the real serial path.

This is the only place the device wire protocol lives. The codec module owns the
encode and decode of the RS232 command format, and the transport module drives it
over pyserial. Nothing above transport sees these bytes.
"""
