"""Shared base model and global Pydantic configuration for the contract.

Every contract model inherits from ContractModel, which fixes the two
conventions that apply package wide:

- extra="forbid" so unknown fields are rejected at the client/server seam.
- frozen=True so request and reply values do not mutate after construction.

Because model_config merges across inheritance, subclasses inherit this
configuration and do not redeclare it.

Strictness note: no model in this package sets strict=True anywhere. This is a
deliberate softening of knowledge-transfer decision 7 ("use strict models where
practical") for the model_dump(mode="json") seam, not drift. Across that seam a
float field legitimately receives integer JSON (for example 20 for 20 mA) and an
IntEnum field arrives as its integer value; lax validation accepts both, while
global strict mode would reject them. Targeted per-field strictness, added
together with JSON round-trip tests, is a possible later refinement.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Base for every contract model: forbids unknown fields and is frozen."""

    model_config = ConfigDict(extra="forbid", frozen=True)
