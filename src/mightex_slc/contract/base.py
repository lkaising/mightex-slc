# ------------------------------------------------------------------------------
#  Filename: base.py
#
#  Purpose: Define the shared frozen base model for contract validation.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Base for every contract model: forbids unknown fields and is frozen.

    Deliberately not strict: across the model_dump(mode="json") seam a float
    field legitimately receives integer JSON and an IntEnum field arrives as
    its integer value, both of which lax validation accepts.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
