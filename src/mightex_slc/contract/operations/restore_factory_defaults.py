# ------------------------------------------------------------------------------
#  Filename: restore_factory_defaults.py
#
#  Purpose: Define request and reply models for restoring factory-default settings.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from .base import DeviceRequest


class RestoreFactoryDefaultsRequest(DeviceRequest):
    """Load factory defaults into the current settings of all channels and modes.

    This changes the current (volatile) settings only; persist_settings writes
    them to non-volatile memory.
    """


class RestoreFactoryDefaultsOk(ContractModel):
    """Factory defaults restored successfully."""

    status: Literal["ok"] = "ok"


RestoreFactoryDefaultsReply = Annotated[
    RestoreFactoryDefaultsOk | Error, Field(discriminator="status")
]
