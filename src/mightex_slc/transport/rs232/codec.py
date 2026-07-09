# ------------------------------------------------------------------------------
#  Filename: codec.py
#
#  Purpose: Encodes and decodes the RS232 wire format; private to rs232.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The RS232 wire format: every command and response string, in one place.

All of it is pure string-to-string work, which keeps the protocol testable
without hardware. The rs232 transport owns the bytes around these strings
(terminators, buffer hygiene, timing); the client and server deal only in
contract models.

Currents serialize faithfully as whole milliamps: integral values become
their integer text, and a value the wire cannot express exactly is refused
rather than rounded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, NamedTuple

from ...contract import ControllerCapabilities, ModuleType, OperatingMode
from ..base import CommandRejectedError, TransportError

# Sent verbatim. ECHOOFF (host-control entry; PC-Mode on MA/CA) never returns
# a clean ack; DEVICEINFO returns the one bare, un-prefixed response.
ECHO_OFF_COMMAND: Final[str] = "ECHOOFF"
DEVICE_INFO_COMMAND: Final[str] = "DEVICEINFO"


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """The fields a DEVICEINFO response may carry; each None when absent.

    The vendor gives no grammar for this response, only sample strings that
    differ between documents and the real unit, so every field is
    independently optional and the caller decides what a missing one means.
    """

    firmware_version: str | None
    module_number: str | None
    serial_number: str | None


# --- Encoding: operations to command strings (no terminator; framing is I/O) ---


def format_current_ma(value: float) -> str:
    """Serialize a whole-milliamp value as wire integer text."""
    current_ma = float(value)
    if current_ma.is_integer():
        return str(int(current_ma))

    raise CommandRejectedError(f"current {current_ma!r} mA is not a whole-mA value")


def encode_normal(channel: int, current_max_ma: float, current_set_ma: float) -> str:
    """Build the NORMAL command: store Imax/Iset for a channel, output unchanged."""
    imax = format_current_ma(current_max_ma)
    iset = format_current_ma(current_set_ma)
    return f"NORMAL {channel} {imax} {iset}"


def encode_mode(channel: int, mode: OperatingMode) -> str:
    """Build the MODE command: the only command that changes output."""
    return f"MODE {channel} {int(mode)}"


def encode_query_mode(channel: int) -> str:
    """Build the ?MODE query for one channel."""
    return f"?MODE {channel}"


def encode_query_current(channel: int) -> str:
    """Build the ?CURRENT query for one channel's NORMAL parameters."""
    return f"?CURRENT {channel}"


# --- Response classification ---


def check_response(response: str, command: str) -> str:
    """Return stripped response text, raising for known device rejections."""
    text = response.strip()

    if text.startswith("#!"):
        error = f"device reported an execution error for {command!r}: {text!r}"
    elif text.startswith("#?"):
        error = f"device rejected an argument of {command!r}: {text!r}"
    elif "is not defined" in text:
        error = f"device does not know the command {command!r}: {text!r}"
    else:
        return text

    raise CommandRejectedError(error)


def require_ack(response: str, command: str) -> None:
    """Raise unless the response contains the success ack marker."""
    check_response(response, command)

    if "##" in response:
        return

    raise TransportError(f"expected '##' ack for {command!r}, got {response!r}")


# --- Parsing: response strings to values (strip '#', split; never positional) ---


def parse_mode(response: str) -> OperatingMode:
    """Extract the operating mode from a ?MODE response like '#1'."""
    text = response.replace("#", "").strip()

    try:
        return OperatingMode(int(text))
    except ValueError:
        raise TransportError(f"cannot parse an operating mode from {response!r}") from None


def parse_current(response: str) -> tuple[float, float]:
    """Extract (Imax, Iset) in mA from a ?CURRENT response.

    The response leads with two calibration fields ('#Cal1 Cal2 Imax Iset'),
    so the values are the LAST two tokens; a positional parse would read
    calibration data as currents.
    """
    tokens = response.replace("#", "").split()
    if len(tokens) < 2:
        raise TransportError(f"cannot parse NORMAL parameters from {response!r}")
    try:
        # int-strict like the proven parser: the device emits digit strings;
        # nan/inf/decimals would be corruption, not a current.
        return float(int(tokens[-2])), float(int(tokens[-1]))
    except ValueError:
        raise TransportError(f"cannot parse NORMAL parameters from {response!r}") from None


def _field_after(response: str, label: str) -> str | None:
    """The whitespace-delimited word right after a label, or None."""
    if label not in response:
        return None
    tail = response.split(label, 1)[1].split()
    return tail[0] if tail else None


def parse_device_info(response: str) -> DeviceInfo:
    """Parse a DEVICEINFO response by keyword; total, never raises."""
    return DeviceInfo(
        firmware_version=_field_after(response, "Driver:"),
        module_number=_field_after(response, "Module No.:"),
        serial_number=_field_after(response, "Serial No.:"),
    )


# --- Module identity to capabilities ---


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
            f"no documented capabilities for module family {family.name!r} "
            f"in {module_number!r}"
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
