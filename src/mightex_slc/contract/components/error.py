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
    """Operation failure reply.

    A device error code is only attached to DeviceCommandError, and only when
    the controller reports one.
    """

    status: Literal["error"] = "error"
    error_type: ErrorType = Field(
        description="Concrete error type to raise on the client.",
    )
    message: str = Field(
        description="Human-readable failure message.",
    )
    code: int | None = Field(
        default=None,
        description="Device error code, when reported by the controller.",
    )

    @model_validator(mode="after")
    def _code_only_for_device_command(self) -> "Error":
        if self.code is not None and self.error_type is not ErrorType.DEVICE_COMMAND:
            raise ValueError("code is only valid for DeviceCommandError")
        return self
