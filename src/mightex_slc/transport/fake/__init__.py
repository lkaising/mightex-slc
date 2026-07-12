# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The fake backend package: a pure-Python device, no hardware.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The fake backend package.

Home of the pure-Python simulated device that implements the transport interface
with no hardware attached. It lets the client, server, and contract run end to
end before any real controller is in the loop.
"""

from .fake_transport import FakeChannelState, FakeTransport

__all__ = [
    "FakeChannelState",
    "FakeTransport",
]
