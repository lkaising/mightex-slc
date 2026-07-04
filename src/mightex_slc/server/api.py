# ------------------------------------------------------------------------------
#  Filename: api.py
#
#  Purpose: Server entry point that client link calls into.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The server's front door: the entry point client/link.py calls into.

It receives a serialized request (operation name plus data) and hands it to
dispatch. In the current single-process design this is a direct in-process call
rather than a network endpoint, but keeping it as an explicit boundary is
deliberate: if a local socket or daemon is ever added, it slots in here without
the contract or the rest of the stack moving.
"""
