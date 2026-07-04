# ------------------------------------------------------------------------------
#  Filename: link.py
#
#  Purpose: Sends contract requests to the server and parses replies.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The client half of the contract seam, and the busiest file in this layer.

For each call it builds the operation's Pydantic request model, serializes it
with model_dump(mode="json"), calls into the server entry point, then parses the
reply against that operation's reply union. On an ok reply it returns the success
value; on an error reply it maps error_type to an exception and raises it. Every
client method ultimately goes through here.
"""
