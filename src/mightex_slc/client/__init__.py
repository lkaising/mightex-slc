# ------------------------------------------------------------------------------
#  Filename: __init__.py
#
#  Purpose: Public surface of the library; the entry points users import.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The public surface of the library: what a user imports.

This module exposes the top-level entry points (enumerate_devices and
open_device) and re-exports the enums, types, and exception classes users are
meant to reach. If a name is not surfaced here, it is not part of the public
API. It mirrors the top level of the API skeleton.
"""
