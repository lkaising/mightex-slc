# ------------------------------------------------------------------------------
#  Filename: persist_settings.py
#
#  Purpose: Define request and reply models for persisting settings to memory.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..base import ContractModel
from ..components.error import Error
from .base import DeviceRequest


class PersistSettingsRequest(DeviceRequest):
    """Persist the current settings of all channels and modes to non-volatile memory."""


class PersistSettingsOk(ContractModel):
    """Settings persisted successfully."""

    status: Literal["ok"] = "ok"


PersistSettingsReply = Annotated[PersistSettingsOk | Error, Field(discriminator="status")]
