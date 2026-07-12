# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The server package: owns live devices and drives the hardware.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The server package: the low level that owns device state and drives hardware.

Everything here runs in one process. The server receives a request payload,
validates it, routes it to the right live device object, and returns a reply. It
is the mirror of the client: where the client turns calls into requests and
envelopes into exceptions, the server turns requests into device actions and
exceptions into envelopes.
"""
