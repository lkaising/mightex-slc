# ------------------------------------------------------------------------------
#  Filename: codec.py
#
#  Purpose: Encodes and decodes the RS232 wire format; private to rs232.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The private wire format: the one place the RS232 protocol lives.

It encodes device operations into the controller's ASCII command strings and
decodes the responses. It is deliberately kept out of the contract; the client
and server deal in Pydantic models, and only this file knows what the bytes on
the wire look like.

Everything here is pure string-to-string work: no serial port, no timing, no
I/O. That purity is what makes the wire format testable without hardware. The
rs232 transport owns the bytes around these strings — terminators, buffer
hygiene, and timing.

Currents are serialized faithfully as whole milliamps: integral values become
their integer text, and a value the wire format cannot express exactly is
refused rather than rounded. The FA/FV/XA/XV families, whose wire unit is
0.1 mA rather than 1 mA, are refused at open for the same reason — faithful
mA serialization would drive them 10x low, so supporting them needs a
deliberate unit-scaling revisit. The bench SA family is identity-units.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from ...contract import ControllerCapabilities, ModuleType, OperatingMode
from ..base import CommandRejectedError, TransportError

# Parameterless commands, sent verbatim. ECHOOFF is the host-control entry
# (PC-Mode on MA/CA modules) and the one command that never returns a clean
# ack; DEVICEINFO returns the one bare, un-prefixed response string.
ECHO_OFF_COMMAND: Final[str] = "ECHOOFF"
DEVICE_INFO_COMMAND: Final[str] = "DEVICEINFO"


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """The fields a DEVICEINFO response may carry; each None when absent.

    The vendor gives no grammar for this response — only sample strings that
    differ between documents and the real unit — so every field is
    independently optional and the caller decides what a missing one means.
    """

    firmware_version: str | None
    module_number: str | None
    serial_number: str | None


# ---------------------------------------------------------------------------
# Encoding: operations to command strings (no terminator; framing is I/O)
# ---------------------------------------------------------------------------


def format_current_ma(value: float) -> str:
    """Serialize a milliamp value as the integer text the wire expects.

    Faithful serialization only: no rounding, no scaling, no clamping. A value
    that is not a whole number of milliamps cannot be expressed, so it is
    refused as a rejected command rather than silently altered.
    """
    value = float(value)
    if not value.is_integer():
        raise CommandRejectedError(
            f"current {value!r} mA is not a whole-mA value; "
            "this backend sends integer mA"
        )
    return str(int(value))


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


# ---------------------------------------------------------------------------
# Response classification
# ---------------------------------------------------------------------------


def check_response(response: str, command: str) -> str:
    """Raise if the device refused the command; else return the stripped text.

    The response is stripped first so the prefix checks hold on raw reads;
    the checks themselves are prefix/substring matches, deliberately not
    equality, so they tolerate echo remnants and stray line-ending bytes
    around the code. No device error code is ever attached: the vendor's
    post-#! Error command is undocumented, so nothing reports one.
    """
    response = response.strip()
    if response.startswith("#!"):
        raise CommandRejectedError(
            f"device reported an execution error for {command!r}: {response!r}"
        )
    if response.startswith("#?"):
        raise CommandRejectedError(
            f"device rejected an argument of {command!r}: {response!r}"
        )
    if "is not defined" in response:
        raise CommandRejectedError(
            f"device does not know the command {command!r}: {response!r}"
        )
    return response


def require_ack(response: str, command: str) -> None:
    """Require the ## success marker after ruling out explicit refusals.

    A non-empty response that is neither a refusal nor an ack is a protocol
    violation — a link problem, not a device decision — so it raises the root
    transport error.
    """
    check_response(response, command)
    if "##" not in response:
        raise TransportError(f"expected '##' ack for {command!r}, got {response!r}")


# ---------------------------------------------------------------------------
# Parsing: response strings to values (strip '#', split; never positional)
# ---------------------------------------------------------------------------


def parse_mode(response: str) -> OperatingMode:
    """Extract the operating mode from a ?MODE response like '#1'."""
    text = response.replace("#", "").strip()
    try:
        return OperatingMode(int(text))
    except ValueError:
        raise TransportError(
            f"cannot parse an operating mode from {response!r}"
        ) from None


def parse_current(response: str) -> tuple[float, float]:
    """Extract (Imax, Iset) in mA from a ?CURRENT response.

    The response leads with two calibration fields — '#Cal1 Cal2 Imax Iset' —
    so the values are the LAST two tokens; a positional parse would read
    calibration data as currents.
    """
    tokens = response.replace("#", "").split()
    if len(tokens) < 2:
        raise TransportError(f"cannot parse NORMAL parameters from {response!r}")
    try:
        # int-strict like the proven parser: the device emits digit strings,
        # and anything float() would additionally admit (nan, inf, decimals)
        # is a corrupt reply, not a current.
        return float(int(tokens[-2])), float(int(tokens[-1]))
    except ValueError:
        raise TransportError(
            f"cannot parse NORMAL parameters from {response!r}"
        ) from None


def _token_after(response: str, keyword: str) -> str | None:
    """The whitespace-delimited token right after a keyword, or None."""
    if keyword not in response:
        return None
    tail = response.split(keyword, 1)[1].split()
    return tail[0] if tail else None


def parse_device_info(response: str) -> DeviceInfo:
    """Parse a DEVICEINFO response by keyword; total, never raises.

    Sample shapes differ between vendor documents and the real unit (the
    module field is not always present), so each field is looked up by its
    keyword and is None when absent. The caller decides what missing fields
    mean.
    """
    return DeviceInfo(
        firmware_version=_token_after(response, "Driver:"),
        module_number=_token_after(response, "Module No.:"),
        serial_number=_token_after(response, "Serial No.:"),
    )


# ---------------------------------------------------------------------------
# Module identity to capabilities
# ---------------------------------------------------------------------------

# Per-family facts from the vendor user manual's module feature matrix, one
# row per family this backend can drive faithfully. Columns: current
# resolution (mA per count), programmable profile steps, TRIGGER mode,
# load-voltage read-back, FanPWM (further gated to -MU variants below).
# Step counts: the vendor's "128 Steps" includes the mandatory (0, 0)
# terminator pair (its own text says "allows 127 programmable maximum
# steps"), hence 127 here. Whether the "2 Steps" families likewise lose one
# pair to the terminator is unresolved and out of this slice's scope; 2
# matches the matrix figure and the existing fake's convention.
# Deliberately absent, so opening one fails rather than guessing or lying:
# QA (no vendor matrix row, undocumented resolution) and FA/FV/XA/XV (their
# wire unit is 0.1 mA, which this codec's whole-mA serialization would drive
# 10x low — see the module docstring).
_FAMILY_TABLE: Final[dict[ModuleType, tuple[float, int, bool, bool, bool]]] = {
    ModuleType.AA: (1.0, 127, True, False, False),
    ModuleType.AV: (1.0, 127, True, True, False),
    ModuleType.SA: (1.0, 2, True, False, False),
    ModuleType.SV: (1.0, 2, True, True, False),
    ModuleType.MA: (1.0, 2, False, False, True),
    ModuleType.CA: (5.0, 2, False, False, True),
    ModuleType.HA: (1.0, 2, True, False, False),
    ModuleType.HV: (1.0, 2, True, True, False),
}

# Family letters and channel count out of a module number like SLC-SA04-U/S
# or SLC-MA04-MU (SLB-prefixed variants exist for the H families).
_MODULE_PATTERN: Final[re.Pattern[str]] = re.compile(r"-([A-Z]{2})(\d{2})")


def capabilities_for_module(module_number: str | None) -> ControllerCapabilities:
    """Map a DEVICEINFO module number onto the family capability table.

    Takes the module token DEVICEINFO reported (e.g. 'SLC-SA04-U/S'). Raises
    the root transport error when the module is missing, does not parse, or
    names a family with no capability row this backend can drive faithfully;
    the library never fabricates device facts.
    """
    if module_number is None:
        raise TransportError("device did not report a module number")
    normalized = module_number.upper()
    match = _MODULE_PATTERN.search(normalized)
    if match is None:
        raise TransportError(f"cannot identify a module family in {module_number!r}")
    family_text, channel_text = match.groups()
    try:
        family = ModuleType[family_text]
    except KeyError:
        raise TransportError(
            f"unknown module family {family_text!r} in {module_number!r}"
        ) from None
    row = _FAMILY_TABLE.get(family)
    if row is None:
        raise TransportError(
            f"module family {family_text!r} has no documented capabilities; "
            f"refusing to guess for {module_number!r}"
        )
    channel_count = int(channel_text)
    if channel_count < 1:
        raise TransportError(
            f"implausible channel count {channel_count} in {module_number!r}"
        )
    resolution_ma, profile_steps, trigger, load_voltage, fan = row
    # FanPWM hardware exists only on the -MU knob variants of MA/CA.
    fan = fan and "-MU" in normalized
    return ControllerCapabilities(
        module_type=family,
        channel_count=channel_count,
        current_resolution_ma=resolution_ma,
        max_profile_steps=profile_steps,
        supports_trigger_mode=trigger,
        supports_load_voltage=load_voltage,
        supports_fan_control=fan,
    )
