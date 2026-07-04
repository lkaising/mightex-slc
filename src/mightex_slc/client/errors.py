# ------------------------------------------------------------------------------
#  Filename: errors.py
#
#  Purpose: Exception hierarchy the client raises from error replies.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The exception hierarchy the client raises, rooted at MightexLEDError.

The tree covers connection, not-found, command, unsupported-operation, and
controller-closed errors. These are raised on the client side: when a reply comes
back as an error envelope, link reads its error_type and raises the matching class
from here. It is the human-facing error vocabulary, the counterpart to the
server's exception-to-envelope mapping.
"""
