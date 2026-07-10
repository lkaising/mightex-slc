# ------------------------------------------------------------------------------
#  Filename: capabilities.py
#
#  Purpose: Maps module identity to documented capabilities; private to rs232.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
Module identity to documented capabilities: the vendor manual's module
feature matrix, as this backend can honor it.

This is per-backend knowledge rather than global device truth: a family
earns a row only when the rs232 wire format drives it faithfully, and an
unknown or excluded family refuses the open rather than guessing. The
exclusions and the step-count reading are justified at the table below.
"""

from __future__ import annotations

import re
from typing import Final, NamedTuple

from ...contract import ControllerCapabilities, ModuleType
from ..base import TransportError


class _Family(NamedTuple):
    """One capability row of the vendor manual's module feature matrix."""

    resolution_ma: float
    profile_steps: int
    trigger: bool
    load_voltage: bool
    fan_pwm: bool


# One row per family this backend can drive faithfully. The vendor's
# "128 Steps" includes the mandatory (0, 0) terminator pair (its own text
# says "allows 127 programmable maximum steps"), hence 127; whether the
# "2 Steps" families also lose a pair is unresolved, so 2 matches the matrix
# figure and the existing fake. Deliberately absent, so opening one fails
# rather than guessing: QA (no matrix row, undocumented resolution) and
# FA/FV/XA/XV (wire unit 0.1 mA, which whole-mA serialization would drive
# 10x low).
_FAMILY_TABLE: Final[dict[ModuleType, _Family]] = {
    ModuleType.AA: _Family(1.0, 127, trigger=True, load_voltage=False, fan_pwm=False),
    ModuleType.AV: _Family(1.0, 127, trigger=True, load_voltage=True, fan_pwm=False),
    ModuleType.SA: _Family(1.0, 2, trigger=True, load_voltage=False, fan_pwm=False),
    ModuleType.SV: _Family(1.0, 2, trigger=True, load_voltage=True, fan_pwm=False),
    ModuleType.MA: _Family(1.0, 2, trigger=False, load_voltage=False, fan_pwm=True),
    ModuleType.CA: _Family(5.0, 2, trigger=False, load_voltage=False, fan_pwm=True),
    ModuleType.HA: _Family(1.0, 2, trigger=True, load_voltage=False, fan_pwm=False),
    ModuleType.HV: _Family(1.0, 2, trigger=True, load_voltage=True, fan_pwm=False),
}

# Family letters and channel count, as in SLC-SA04-U/S or SLC-MA04-MU
# (SLB-prefixed variants exist for the H families).
_MODULE_PATTERN: Final[re.Pattern[str]] = re.compile(r"-([A-Z]{2})(\d{2})")


def _parse_module_number(module_number: str) -> tuple[ModuleType, int]:
    """Return the module family and channel count encoded in a module number."""
    match = _MODULE_PATTERN.search(module_number.upper())
    if match is None:
        raise TransportError(f"cannot identify a module family in {module_number!r}")

    family_name, channel_count = match.groups()

    try:
        family = ModuleType[family_name]
    except KeyError:
        raise TransportError(
            f"unknown module family {family_name!r} in {module_number!r}"
        ) from None

    return family, int(channel_count)


def capabilities_for_module(module_number: str | None) -> ControllerCapabilities:
    """Return documented capabilities for a DEVICEINFO module number."""
    if module_number is None:
        raise TransportError("device did not report a module number")

    family, channel_count = _parse_module_number(module_number)
    if channel_count < 1:
        raise TransportError(f"implausible channel count {channel_count} in {module_number!r}")

    row = _FAMILY_TABLE.get(family)
    if row is None:
        raise TransportError(
            f"no documented capabilities for module family {family.name!r} in {module_number!r}"
        )

    module_upper = module_number.upper()
    supports_fan_control = row.fan_pwm and "-MU" in module_upper

    return ControllerCapabilities(
        module_type=family,
        channel_count=channel_count,
        current_resolution_ma=row.resolution_ma,
        max_profile_steps=row.profile_steps,
        supports_trigger_mode=row.trigger,
        supports_load_voltage=row.load_voltage,
        supports_fan_control=supports_fan_control,
    )
