# Architecture

How the library is put together: the layers, the seams between them, and the
decisions that are settled. Device and wire-protocol facts live in
[`protocol.md`](protocol.md).

---

## 1. Design goals

A Python library for Mightex SLC-series LED controllers with three
properties:

1. **A protocol-neutral public API.** No raw command or wire-protocol detail
   in any signature. The one place serial reality is visible is the open
   boundary: `open_device("/dev/ttyUSB0")` names the serial target
   explicitly, and `open_fake_device()` is the explicit no-hardware spelling.
   Past open, users see `Controller` and `Channel` objects; whether the
   transport is the fake or the real RS232 driver — and whether the server is
   in-process or (someday) behind a socket — is invisible.
2. **A validated contract seam.** Every operation crosses a client→server
   boundary as a plain JSON-mode dict, built from and re-validated against
   shared Pydantic models. Kept honest even in-process, so a later daemon
   (the deferred fix for single-owner serial ports) is a wiring change, not a
   contract change.
3. **Fake-first development.** The whole stack runs against an in-memory fake
   device. Hardware is required only to validate the RS232 backend itself.

Standing rule: **every asserted device fact traces to the vendor documents or
hardware evidence, or is explicitly labeled a library convention.** That is
what the [V]/[HW]/[C] tags in [`protocol.md`](protocol.md) record.

## 2. The five layers

```
contract/            pure Pydantic models — depends on nothing
   ▲
transport/base       the small interface the server drives
   ▲
transport/fake       in-memory device        transport/rs232   real serial device
   ▲
server/              sessions + device impl; validates with contract, drives transport
   ▲
client/              stateless proxies; builds requests, parses replies, raises
   ▲
mightex_slc/__init__ the assembled public surface
```

- **`contract/`** — one `Request`/`Ok`/`Reply` model triple per operation,
  shared component models (enums, descriptors, capabilities), all frozen with
  extra fields forbidden (`ContractModel`). The single source of truth for
  what crosses the seam. Schema YAML in `schemas/` is generated *from* these
  models (never edited) by `scripts/generate_schemas.py`.
- **`transport/`** — `base.py` defines what the server needs: open the
  controller at a serial-port target (returning a handle plus capabilities),
  issue per-device/per-channel commands, close. `fake/` implements it in
  memory; `rs232/` implements it against the real device (§6).
- **`server/`** — owns live state. `api.py` is the single entry point;
  `dispatch.py` reconstructs and re-validates the request model (the trust
  boundary) and routes by operation name; `session.py` maps `device_id` →
  live handle; `impl/controller.py` and `impl/channel.py` are the real device
  model driving the transport; `errors.py` converts failures into the `Error`
  envelope.
- **`client/`** — `link.py` is the seam client-side: stateless functions over
  a caller-supplied executor — build model → `model_dump(mode="json")` →
  `executor.handle(...)` → parse reply → map `error_type` to an exception.
  `controller.py` holds `open_device` / `open_fake_device` and the
  `Controller` proxy they construct; `channel.py` is the thin `Channel`
  proxy; `types.py` re-exports contract shapes; `errors.py` holds the
  exception hierarchy.

The client holds no module state anywhere. `open_device` resolves the request
executor exactly once — wrapping the transport in an in-process `Server` —
and pins it to the `Controller` it returns, so a `device_id` and the executor
whose session minted it always travel together and every later call,
including close, deterministically reaches the same server. That keeps the
seam a real boundary.

**Two seams, two questions.** The stack has two independent injection points,
and the vocabulary keeps them apart:

| Term | Question it answers |
|---|---|
| `Transport` | what device is behind the server: the real RS232 driver or the in-memory fake |
| `RequestExecutor` | where the server is and how requests reach it: an in-process object today, a socket someday |
| `Server` | the current in-process `RequestExecutor` implementation |
| `Controller` | a client proxy pinned to one `RequestExecutor` and one `device_id` |

The invariant that keeps the eventual daemon a wiring change: **`link.py` is
typed against `RequestExecutor` and never against `Transport`;
`Server(transport)` is constructed in the client's `open_device` and nowhere
deeper.** The transport being the public injection point (`transport=`) must
not erode the executor seam being the architectural boundary. A daemon client
is a new `RequestExecutor` implementation plus one additively introduced
public injection point; no existing call site changes.

## 3. The public API surface

The full reference lives in [`../using/api.md`](../using/api.md); the shape
in one glance:

```python
import time

from mightex_slc import NormalParameters, OperatingMode, open_device

with open_device(port="/dev/ttyUSB0") as controller:  # -> Controller (context manager)
    channel = controller.channel(1)                   # one-based; pure client-side accessor
    channel.set_normal_parameters(NormalParameters(current_max_ma=200.0, current_set_ma=100.0))
    channel.set_active_mode(OperatingMode.NORMAL)     # light on
    try:
        time.sleep(5.0)                               # timed-on is host-timed (no device primitive)
    finally:
        channel.set_active_mode(OperatingMode.DISABLE)  # light off
# context exit closes the device
```

Decisions this shape encodes:

- `open_device` targets a serial port; there is no enumeration and no port
  scanning. Probing a port is a side-effecting act (opening sends ECHOOFF,
  which enters PC Mode on MA/CA-MU variants), so the user names the port.
  Omitting it raises a client-side `ValueError` unless a transport is
  injected explicitly: `open_device("/dev/ttyUSB0")` and `open_fake_device()`
  are the two normal spellings, and `open_device(transport=...)` is the
  advanced/testing seam, accepting any `Transport` (the port passes through;
  the fake accepts and ignores it). Nothing is ever read from the
  environment, and the fake is never selected by omission.
- There is no `initialize()` operation: host-control entry (ECHOOFF) is part
  of `open_device` itself, which is why opening is documented as
  side-effecting.
- `Controller` caches the `ControllerCapabilities` returned by open, so
  capability questions answer without a round trip.
- `channel(n)` never crosses the seam; it just constructs a `Channel` proxy
  carrying the controller's executor, its `device_id`, and `n`.
- `set_normal_parameters` takes a `NormalParameters` model carrying
  `current_max_ma` / `current_set_ma` floats in mA; the model refuses
  `current_set_ma > current_max_ma` (and negative currents) at construction,
  and nothing rescales or rounds the values. The rs232 backend serializes them
  faithfully and refuses what the wire cannot express (non-whole mA, and the
  0.1 mA-unit F*/X* families at open) rather than silently reinterpreting.
- `OperatingMode` is an `IntEnum` with the device's own codes: DISABLE=0,
  NORMAL=1, STROBE=2, TRIGGER=3. These serialize as plain ints on the wire
  (`{"device_id": …, "channel": 1, "mode": 1}`).

## 4. Error model

Public hierarchy (client-side):

```
MightexLEDError
├── DeviceConnectionError
│   └── DeviceNotFoundError
├── DeviceCommandError        (carries optional device `code`)
├── UnsupportedOperationError
└── ControllerClosedError
```

Plus plain `ValueError` for argument validation, raised client-side and not
part of the contract. The contract's `ErrorType` enum holds exactly these
five leaf names as strings, so `link` maps an error reply back to the right
exception class mechanically.

Errors surface in three distinct places:

1. **Client-side at request construction** — invalid arguments fail Pydantic
   validation before anything crosses the seam: set > max and negative
   currents at `NormalParameters` construction, channel < 1 when `link`
   builds the request model.
2. **Server-side re-validation in `dispatch`** — the trust boundary; inert
   with a well-behaved in-process client, load-bearing for any future
   untrusted caller.
3. **Device/execution failures** — returned as an `Error` reply
   (`status="error"`, `error_type`, `message`, optional `code`) and re-raised
   client-side. Note the device itself reports execution failure as a single
   undifferentiated condition (`#!`), so most device errors become
   `DeviceCommandError`.

## 5. The fake transport

The fake is not a mock — it is a tiny model of the device that encodes the
semantics in [`protocol.md`](protocol.md) §6:

- One controller with a module family, ≥1 channels, a current resolution, and
  per-channel state: active mode, stored NORMAL `Imax`/`Iset`, stored TRIGGER
  `Imax`/polarity, and a stored trigger profile.
- `set_normal_parameters` stores parameters **without changing output**;
  `get_normal_parameters` reads the stored pair back;
  `set_active_mode` is what "lights the LED" (mutates active mode);
  `get_active_mode` reads the live mode back. The trigger set/get pairs work
  the same way — configuration never changes output.
- Trigger configuration mimics the bench-measured device: it is never
  rejected, it **silently clamps** (an over-ceiling TRIGGER `Imax` to the
  pulsed ceiling; profile step currents to the `Imax` stored at write time),
  so the verify-by-read-back workflow is exercisable without hardware.
- `restore_factory_defaults` resets every channel to the factory defaults
  (which changes output — active channels go to DISABLE);
  `persist_settings` acknowledges without effect, because the fake models
  no power cycle where persisted state could be observed.
- The simulated device is chosen by a persona at construction. The default
  (and what `open_fake_device()` uses) is an MA04-MU, which keeps the
  no-trigger capability path exercised; an SA04-like trigger-capable persona
  mirrors the bench unit, including its measured trigger factory defaults.
  The personas' exact values are documented in
  [`../using/api.md`](../using/api.md).
- Channel state persists across close — mirroring the real device, which
  keeps driving its outputs when the serial port closes — so an end state
  stays inspectable after a run.

Because the fake models device semantics, a NORMAL-mode script's end state
(stored parameters match, mode is DISABLE after the `finally`) can be checked
without hardware, with the full client → server → transport stack in play.

## 6. The RS232 backend

Implemented in `transport/rs232/` and hardware-verified on a bench
SLC-SA04-U/S — an LED driven on and off through the public API.

**Division of labor:**

- `rs232_transport.py` — the `Transport` implementation: handle lifecycle,
  the identify flow (ECHOOFF, then DEVICEINFO), per-operation orchestration.
- `serial_link.py` — owns the pyserial port, framing, and timing. Knows
  bytes, not meaning.
- `codec.py` — pure functions: build command strings (`"NORMAL 1 200 100"`),
  parse/validate responses. Knows meaning, not I/O. Keeping the codec pure is
  what makes the protocol testable against a scripted serial object; preserve
  that property.
- `capabilities.py` — maps the DEVICEINFO module number to the vendor
  matrix's documented capabilities; unknown families refuse rather than
  guess.

The byte-level recipe the backend implements (terminators, drain, buffer
hygiene, ack rules) is the hardware-proven one documented in
[`protocol.md`](protocol.md) §§2–4 and §8.

Behavioral obligations the backend and its callers observe: disable channels
in `finally` (the device keeps driving LEDs after the port closes), and
program → verify → only then `STORE` (though nothing in the library sends
`STORE` today). Deliberately absent: thread safety and retries — strict
request/reply plus the buffer hygiene above is why no-retries works.

**Choosing the transport.** There is no factory and no environment variable:
the transport is always constructed explicitly. `open_device("/dev/ttyUSB0")`
builds an `RS232Transport` privately; `open_fake_device()` is the fake,
explicit by name; `open_device(transport=...)` injects any `Transport` — the
way to wrap the full real stack (dispatch, session, capability policy) around
a `FakeTransport` or a scripted-serial `RS232Transport`. Opening the same
physical serial port twice is not supported: the rs232 open asks the OS for
exclusive ownership where the platform supports it (POSIX flock via
pyserial's `exclusive` flag; Windows ports are exclusive at the OS open
already) and surfaces the refusal as a connection error.

## 7. Deliberate cuts (settled — do not reopen)

- **No message broker, no sockets, no daemon — yet.** Single producer, single
  consumer, in-process. The single-owner-serial-port problem is real but
  deferred; the seam design makes the eventual daemon a wiring change.
- **No C++/vendor-DLL binding.** The SDK confirms its `SendCommand` passthrough
  uses the identical ASCII command set, so raw serial loses nothing.
- **No second validation layer.** Pydantic models are the only validator at
  the seam; hand-written jsonschema checks would drift.
- **No schema-artifact ecosystem.** `schemas/` YAML is generated documentation,
  kept current by rerunning the generator — nothing more. No consumers, no
  post-hoc refactoring projects, no audits of generated output. The generator
  itself cross-references shared shapes instead of inlining copies — an
  implementation detail of the generator, not an ecosystem.
- **No HID/USB path, ever.** By decision the library interfaces over
  RS232/serial only ([`protocol.md`](protocol.md) §1). Units without an RS232
  path are out of scope — a procurement constraint, not a software one.
- **No port scanning or probing, ever.** No `enumerate_devices()`, no
  `list_serial_ports()`, no `probe_serial_ports()`. The vendor's
  `InitDevices`/`OpenDevice(DeviceIndex)` flow is USB/HID-only; RS232 users
  address the port directly. Probing is not passive — opening a port sends
  ECHOOFF, which enters PC Mode on MA/CA-MU variants — so the library opens
  exactly the port it is given and nothing else.
