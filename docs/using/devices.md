# Supported Devices

The library drives Mightex Sirius SLC-series multi-channel LED controllers
over RS232. It identifies the connected module at open (via `DEVICEINFO`)
and reports its documented capabilities as
[`controller.capabilities`](api.md#controllercapabilities).

## Module families

The family and channel count are encoded in the module number — for example
`SLC-SA04-U/S` is a 4-channel SA-family unit. Capabilities by family, from
the vendor's module matrix:

| Family | Current resolution | Profile steps | TRIGGER mode | Load-voltage read-back | Fan control |
|---|---|---|---|---|---|
| AA | 1 mA | 127 | yes | no | no |
| AV | 1 mA | 127 | yes | yes | no |
| SA | 1 mA | 2 | yes | no | no |
| SV | 1 mA | 2 | yes | yes | no |
| MA | 1 mA | 2 | no | no | -MU models only |
| CA | 5 mA | 2 | no | no | -MU models only |
| HA | 1 mA | 2 | yes | no | no |
| HV | 1 mA | 2 | yes | yes | no |

Notes:

- Fan (FanPWM) hardware ships only on the `-MU` knob variants of MA and CA,
  so `supports_fan_control` is reported only for module numbers containing
  `-MU`.
- The vendor's "128 steps" includes the mandatory `(0, 0)` profile
  terminator, so 127 steps are programmable.
- SLB-prefixed variants exist for the H families.

**Not supported:** FA, FV, XA, and XV modules (they use 0.1 mA wire units,
which the backend's whole-milliamp serialization cannot express faithfully)
and QA modules (the vendor documents no capability row or current resolution
for them). Opening one raises a connection-time error rather than guessing.

## Current ceilings

Each family has hard output ceilings, per the vendor manual. The library does
not enforce them — the device rejects values it cannot accept — but they
matter when choosing `current_max_ma`:

| Family | NORMAL mode | STROBE / TRIGGER |
|---|---|---|
| AA / AV | 1000 mA | 3500 mA |
| SA / SV | 1000 mA | 3500 mA |
| HA / HV | 2000 mA | 3500 mA |
| MA / CA | 1000 mA (1200 mA on -MU models) | same as NORMAL (no TRIGGER) |

A controller's ceiling is not your LED's limit — see [safety.md](safety.md).

## Connecting

The library talks **RS232 only**, by design. That means the unit must expose
a serial path, in one of three ways:

- an "-S" (RS232) unit, connected directly or through a USB-serial adapter;
- a dual-interface ("X") unit with its slide switch set to RS232 —
  power-cycle the unit after switching;
- the DB9 connector through a USB-serial adapter (this is how the library
  was hardware-verified: an FTDI FT232R adapter appearing as `/dev/ttyUSB0`
  on Linux).

Use a **straight-through** male-to-female DB9 cable, not a null-modem cable.
A USB-only hookup (the front-panel USB jack on, say, an MA04-MU) enumerates
as an HID device and is out of scope.

Serial parameters (9600 baud, 8N1, no flow control) are handled by the
library; you only supply the port path — see
[getting-started.md](getting-started.md#finding-your-serial-port).

## Hardware verification status

The library is hardware-verified against an **SLC-SA04-U/S** (4 channels,
firmware 3.1.8). Other families are configured from the vendor's documented
capability matrix; the full provenance record is in
[../developing/protocol.md](../developing/protocol.md).
