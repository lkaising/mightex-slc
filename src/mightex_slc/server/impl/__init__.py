# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: The real device model package (controller and channel).
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The impl package: the real device model, not proxies.

These are the actual controller and channel objects that enforce capability
policy and drive the transport. The server's session owns them by device_id,
and dispatch calls their methods to carry out each operation.
"""

from .channel import ChannelModel
from .controller import ControllerModel

__all__ = [
    "ChannelModel",
    "ControllerModel",
]
