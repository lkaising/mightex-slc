# ------------------------------------------------------------------------------
#  Filename: errors.py
#
#  Purpose: Maps raised exceptions to the contract Error envelope.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The exception-to-envelope mapper, counterpart to the client's errors module.

When the device model or validation raises, this turns that exception into an
Error reply: it sets the status, the error_type from the exception class, the
message, and the code when the device reported one. Together with the client's
error module, it lets an exception raised deep in the server surface as the same
exception type on the client.
"""
