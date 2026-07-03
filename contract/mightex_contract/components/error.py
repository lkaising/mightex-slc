"""Shared error reply envelope returned by every operation.

Every operation reply is a discriminated union of that operation's success model
and the shared Error model defined here. The per-operation success models live
with their operations, not here, because read operations carry result data.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from mightex_contract.base import ContractModel
from mightex_contract.components.error_type import ErrorType


class Error(ContractModel):
    """Error reply envelope shared by every operation.

    Runtime-only rule (does not export to JSON Schema): code is populated only
    for DeviceCommandError. It may still be None for a DeviceCommandError when
    the device reports no code.
    """

    status: Literal["error"] = "error"
    error_type: ErrorType = Field(description="Library exception name to raise")
    message: str = Field(description="Human-readable error description")
    # code carries the device-reported error code and is populated only for
    # DeviceCommandError; it is None for every other error type, and may still be
    # None for a DeviceCommandError when the device reports no code.
    code: int | None = Field(
        default=None,
        description="Device-reported error code, present only for DeviceCommandError",
    )

    @model_validator(mode="after")
    def _code_only_for_device_command(self) -> "Error":
        # Runtime-only cross-field rule (KT decision 9); does not export to JSON
        # Schema. A code is meaningful only for DeviceCommandError.
        if self.code is not None and self.error_type is not ErrorType.DEVICE_COMMAND:
            raise ValueError("code is only valid for DeviceCommandError")
        return self
