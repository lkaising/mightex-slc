# ------------------------------------------------------------------------------
#  Filename: codec.py
#
#  Purpose: Encodes and decodes the RS232 wire format; private to rs232.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The private wire format: the one place the RS232 protocol lives.

It encodes device operations into the controller's ASCII command strings and
decodes the responses. It is deliberately kept out of the contract; the client
and server deal in Pydantic models, and only this file knows what the bytes on
the wire look like.
"""
