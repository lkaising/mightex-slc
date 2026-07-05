# ------------------------------------------------------------------------------
#  Filename: error.py
#
#  Purpose: Define the shared error reply envelope for operation failures.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..base import ContractModel
from .error_type import ErrorType


class Error(ContractModel):
    """Error reply envelope shared by every operation.

    Runtime-only rule (does not export to JSON Schema): code is populated only
    for DeviceCommandError. It may still be None for a DeviceCommandError when
    the device reports no code.
    """

    status: Literal["error"] = "error"
    error_type: ErrorType = Field(description="Library exception name to raise")
    message: str = Field(description="Human-readable error description")
    code: int | None = Field(
        default=None,
        description="Device-reported error code, present only for DeviceCommandError",
    )

    @model_validator(mode="after")
    def _code_only_for_device_command(self) -> "Error":
        if self.code is not None and self.error_type is not ErrorType.DEVICE_COMMAND:
            raise ValueError("code is only valid for DeviceCommandError")
        return self
