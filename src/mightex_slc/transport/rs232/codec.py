# ------------------------------------------------------------------------------
#  Filename: codec.py
#
#  Purpose: Encodes and decodes the RS232 wire format; private to rs232.
#
#  Copyright (C) 2026 Logan Kaising.  All rights reserved.
# ------------------------------------------------------------------------------

"""
The RS232 wire format: every command and response string, in one place.

Every command gets exactly one name here: an encode_* function when it takes
arguments, or a *_COMMAND constant when the transport sends it verbatim. No
module outside this one spells a wire string.

All of it is pure string-to-string work, which keeps the protocol testable
without hardware. The serial_link module owns the bytes around these strings
(terminators, buffer hygiene, timing); the client and server deal only in
contract models.

Currents serialize faithfully as whole milliamps: integral values become
their integer text, and a value the wire cannot express exactly is refused
rather than rounded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ...contract import (
    FollowerProfile,
    NormalParameters,
    OperatingMode,
    ProfileStep,
    StepProfile,
    TriggerParameters,
    TriggerPolarity,
)
from ...contract.components.profiles import FOLLOWER_SENTINEL_DURATION_US
from ..base import CommandRejectedError, TransportError

ECHO_OFF_COMMAND: Final[str] = "ECHOOFF"
DEVICE_INFO_COMMAND: Final[str] = "DEVICEINFO"
STORE_COMMAND: Final[str] = "STORE"
RESTORE_DEF_COMMAND: Final[str] = "RESTOREDEF"


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Fields parsed from a DEVICEINFO response."""

    firmware_version: str | None
    module_number: str | None
    serial_number: str | None


# --- Command encoding ---


def encode_normal(channel: int, parameters: NormalParameters) -> str:
    """Build the NORMAL command: store Imax/Iset for a channel, output unchanged."""
    imax = _format_current_ma(parameters.current_max_ma)
    iset = _format_current_ma(parameters.current_set_ma)
    return f"NORMAL {channel} {imax} {iset}"


def _format_current_ma(value: float) -> str:
    """Serialize a whole-milliamp value as wire integer text."""
    current_ma = float(value)
    if current_ma.is_integer():
        return str(int(current_ma))

    raise CommandRejectedError(f"current {current_ma!r} mA is not a whole-mA value")


def encode_mode(channel: int, mode: OperatingMode) -> str:
    """Build the MODE command: the only command that changes output."""
    return f"MODE {channel} {int(mode)}"


def encode_query_mode(channel: int) -> str:
    """Build the ?MODE query for one channel."""
    return f"?MODE {channel}"


def encode_query_current(channel: int) -> str:
    """Build the ?CURRENT query for one channel's NORMAL parameters."""
    return f"?CURRENT {channel}"


def encode_trigger(channel: int, parameters: TriggerParameters) -> str:
    """Build the TRIGGER command: store Imax/polarity for a channel, output unchanged."""
    imax = _format_current_ma(parameters.current_max_ma)
    return f"TRIGGER {channel} {imax} {int(parameters.polarity)}"


def encode_query_trigger(channel: int) -> str:
    """Build the ?TRIGGER query for one channel's TRIGGER parameters."""
    return f"?TRIGGER {channel}"


def encode_trigger_profile(channel: int, profile: StepProfile | FollowerProfile) -> list[str]:
    """Build the full TRIGP command sequence for one profile, terminator included.

    A follower profile becomes the device's reserved first-step spelling —
    the only place the 9999 sentinel reaches the wire. Every sequence ends
    with the mandatory (0, 0) terminator step.
    """
    if isinstance(profile, FollowerProfile):
        current = _format_current_ma(profile.current_ma)
        commands = [f"TRIGP {channel} 0 {current} {FOLLOWER_SENTINEL_DURATION_US}"]
    else:
        commands = [
            f"TRIGP {channel} {index} {_format_current_ma(step.current_ma)} {step.duration_us}"
            for index, step in enumerate(profile.steps)
        ]
    commands.append(f"TRIGP {channel} {len(commands)} 0 0")
    return commands


def encode_query_trigger_profile(channel: int) -> str:
    """Build the ?TRIGP query for one channel's trigger profile."""
    return f"?TRIGP {channel}"


# --- Response validation ---


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


# --- Response decoding ---


def parse_mode(response: str) -> OperatingMode:
    """Extract the operating mode from a ?MODE response like '#1'."""
    text = response.replace("#", "").strip()

    try:
        return OperatingMode(int(text))
    except ValueError:
        raise TransportError(f"cannot parse an operating mode from {response!r}") from None


def parse_current(response: str) -> NormalParameters:
    """Extract stored NORMAL parameters from the final two ?CURRENT response tokens."""
    tokens = response.replace("#", "").split()
    if len(tokens) < 2:
        raise TransportError(f"cannot parse NORMAL parameters from {response!r}")

    max_current_text, set_current_text = tokens[-2:]

    try:
        return NormalParameters(
            current_max_ma=float(int(max_current_text)),
            current_set_ma=float(int(set_current_text)),
        )
    except ValueError:
        raise TransportError(f"cannot parse NORMAL parameters from {response!r}") from None


def parse_trigger(response: str) -> TriggerParameters:
    """Extract stored TRIGGER parameters from a ?TRIGGER response like '#40 0'.

    Unlike ?CURRENT there are no leading calibration fields, but the proven
    last-two-tokens rule is kept for the same junk tolerance. The device can
    hold a polarity this library never writes (it stores any polarity byte
    verbatim); reading one back is a protocol violation, not a parameter set.
    """
    tokens = response.replace("#", "").split()
    if len(tokens) < 2:
        raise TransportError(f"cannot parse TRIGGER parameters from {response!r}")

    max_current_text, polarity_text = tokens[-2:]

    try:
        return TriggerParameters(
            current_max_ma=float(int(max_current_text)),
            polarity=TriggerPolarity(int(polarity_text)),
        )
    except ValueError:
        raise TransportError(f"cannot parse TRIGGER parameters from {response!r}") from None


def parse_trigger_profile(response: str) -> StepProfile | FollowerProfile:
    """Reconstruct a trigger profile from a multi-line ?TRIGP response.

    The bench-derived grammar (protocol.md quirk #9): one 'Iset Tset' line
    per step, '#' on the first line only, and the dump ends at the (0, 0)
    terminator line — which must be present, or the response was truncated.
    Parsed in the proven tolerant style: strip '#', split into tokens, take
    pairs until (0, 0). A first step carrying the reserved follower duration
    reads back as a FollowerProfile, mirroring how the device would play it.
    """

    def unparseable() -> TransportError:
        return TransportError(f"cannot parse a trigger profile from {response!r}")

    tokens = response.replace("#", "").split()
    if not tokens or len(tokens) % 2:
        raise unparseable()

    try:
        pairs = [
            (int(current_text), int(duration_text))
            for current_text, duration_text in zip(tokens[::2], tokens[1::2], strict=True)
        ]
    except ValueError:
        raise unparseable() from None

    if (0, 0) not in pairs:
        raise unparseable()  # no terminator: the read was cut short
    steps = pairs[: pairs.index((0, 0))]

    try:
        if steps and steps[0][1] == FOLLOWER_SENTINEL_DURATION_US:
            return FollowerProfile(current_ma=float(steps[0][0]))
        return StepProfile(
            steps=tuple(
                ProfileStep(current_ma=float(current), duration_us=duration)
                for current, duration in steps
            )
        )
    except ValueError:
        raise unparseable() from None


def parse_device_info(response: str) -> DeviceInfo:
    """Parse a DEVICEINFO response by keyword, returning missing fields as None."""
    return DeviceInfo(
        firmware_version=_field_after(response, "Driver:"),
        module_number=_field_after(response, "Module No.:"),
        serial_number=_field_after(response, "Serial No.:"),
    )


def _field_after(response: str, label: str) -> str | None:
    """Return the whitespace-delimited field after label, or None."""
    if label not in response:
        return None

    fields = response.split(label, 1)[1].split()
    return fields[0] if fields else None
