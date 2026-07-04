# ------------------------------------------------------------------------------
#  Filename: dispatch.py
#
#  Purpose: Validates a request, routes by operation, returns a reply.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The router and the server-side validation point.

It validates an incoming request by constructing the matching Pydantic request
model, which rejects unknown fields and enforces the bounds and cross-field
rules. It then routes by operation name to the right handler on the live device
object, takes the result, and wraps it in the operation's reply model. This is
where an operation name plus a payload becomes a call on the right controller.
"""
