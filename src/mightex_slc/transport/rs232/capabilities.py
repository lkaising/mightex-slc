# ------------------------------------------------------------------------------
#  Filename: capabilities.py
#
#  Purpose: Maps module identity to documented capabilities; private to rs232.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Final, NamedTuple

from ...contract import ControllerCapabilities, ModuleType
from ..base import TransportError


class _FamilyCapabilities(NamedTuple):
    """Capabilities shared by every module in a family."""

    resolution_ma: float
    profile_steps: int
    trigger: bool
    load_voltage: bool
    fan_pwm: bool


# Family letters and channel count, as in SLC-SA04-U/S or SLC-MA04-MU.
# SLB-prefixed variants exist for the H families.
_MODULE_PATTERN: Final[re.Pattern[str]] = re.compile(r"-([A-Z]{2})(\d{2})")


# The vendor's "128 Steps" includes the mandatory (0, 0) terminator, leaving
# 127 programmable steps. Whether the "2 Steps" families also lose a step is
# undocumented, so their published value is retained.
#
# Deliberately excluded:
# - QA: no capability-matrix row or documented resolution.
# - FA/FV/XA/XV: use 0.1 mA wire units, which this backend cannot serialize
#   faithfully using its whole-mA representation.
_FAMILY_TABLE: Final[dict[ModuleType, _FamilyCapabilities]] = {
    ModuleType.AA: _FamilyCapabilities(1.0, 127, trigger=True, load_voltage=False, fan_pwm=False),
    ModuleType.AV: _FamilyCapabilities(1.0, 127, trigger=True, load_voltage=True, fan_pwm=False),
    ModuleType.SA: _FamilyCapabilities(1.0, 2, trigger=True, load_voltage=False, fan_pwm=False),
    ModuleType.SV: _FamilyCapabilities(1.0, 2, trigger=True, load_voltage=True, fan_pwm=False),
    ModuleType.MA: _FamilyCapabilities(1.0, 2, trigger=False, load_voltage=False, fan_pwm=True),
    ModuleType.CA: _FamilyCapabilities(5.0, 2, trigger=False, load_voltage=False, fan_pwm=True),
    ModuleType.HA: _FamilyCapabilities(1.0, 2, trigger=True, load_voltage=False, fan_pwm=False),
    ModuleType.HV: _FamilyCapabilities(1.0, 2, trigger=True, load_voltage=True, fan_pwm=False),
}


def capabilities_for_module(module_number: str | None) -> ControllerCapabilities:
    """Return documented capabilities for a DEVICEINFO module number."""
    if module_number is None:
        raise TransportError("device did not report a module number")

    family, channel_count = _parse_module_number(module_number)
    if channel_count < 1:
        raise TransportError(f"implausible channel count {channel_count} in {module_number!r}")

    capabilities = _FAMILY_TABLE.get(family)
    if capabilities is None:
        raise TransportError(
            f"no documented capabilities for module family {family.name!r} in {module_number!r}"
        )

    supports_fan_control = capabilities.fan_pwm and "-MU" in module_number.upper()

    return ControllerCapabilities(
        module_type=family,
        channel_count=channel_count,
        current_resolution_ma=capabilities.resolution_ma,
        max_profile_steps=capabilities.profile_steps,
        supports_trigger_mode=capabilities.trigger,
        supports_load_voltage=capabilities.load_voltage,
        supports_fan_control=supports_fan_control,
    )


def _parse_module_number(module_number: str) -> tuple[ModuleType, int]:
    """Return the family and channel count encoded in a module number."""
    match = _MODULE_PATTERN.search(module_number.upper())
    if match is None:
        raise TransportError(f"cannot identify a module family in {module_number!r}")

    family_name, channel_text = match.groups()

    try:
        family = ModuleType[family_name]
    except KeyError:
        raise TransportError(
            f"unknown module family {family_name!r} in {module_number!r}"
        ) from None

    return family, int(channel_text)
