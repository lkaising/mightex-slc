# ------------------------------------------------------------------------------
#  Filename: fake_transport.py
#
#  Purpose: Pure-Python simulated device implementing the transport interface.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
A pure-Python simulated controller implementing the transport interface.

It responds the way a device would, with no hardware attached. This is what the
integration test runs against, and what lets the client, server, and contract be
exercised end to end before any real controller is connected.
"""
