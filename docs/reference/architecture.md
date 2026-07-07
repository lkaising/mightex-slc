# mightex-slc — Architecture

Status: source of truth as of 2026-07-06. Describes the design the current
repo skeleton encodes and the `normal_mode_timed_on` slice proves. Device
facts live in `device_and_protocol.md`; the step-by-step build order lives in
`build_plan_normal_mode_timed_on.md`.

---

## 1. Vision

A Python library for Mightex SLC LED controllers with three properties:

1. **A protocol-neutral public API.** No raw command or wire-protocol detail
   in any signature. The one place serial reality is visible is the open
   boundary: `open_device(port=...)` names the serial target explicitly when
   opening an RS232-backed controller (`None` means the backend's configured
   default). Past open, users see `Controller` and `Channel` objects; whether
   the backend is a fake, an in-process RS232 driver, or (someday) a socket
   to a daemon is invisible.
2. **A validated contract seam.** Every operation crosses a client→server
   boundary as a plain JSON-mode dict, built from and re-validated against
   shared Pydantic models. Kept honest even in-process, so a later daemon
   (the deferred fix for single-owner serial ports) is a wiring change, not a
   contract change.
3. **Fake-first development.** The whole stack runs against an in-memory fake
   device. Hardware is required only to validate the RS232 backend itself.

And one working method: **slices, not layers-in-full.** Build the smallest
complete vertical through every layer, get it green, then repeat the proven
shape. Breadth-first is what killed the contract branch (see `lineage.md`).

Standing rule inherited from that branch: **every asserted device fact traces
to the vendor documents or hardware evidence, or is explicitly labeled a
library convention.** It exists because a previous draft fabricated device
facts that survived review for days.

## 2. The five layers

```
contract/            pure Pydantic models — depends on nothing
   ▲
transport/base       the small interface the server drives
   ▲
transport/fake       in-memory device        transport/rs232  (later, same interface)
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
  memory; `rs232/` will implement it against the real device (§6).
- **`server/`** — owns live state. `api.py` is the single entry point;
  `dispatch.py` reconstructs and re-validates the request model (the trust
  boundary) and routes by operation name; `session.py` maps `device_id` →
  live handle; `impl/controller.py` and `impl/channel.py` are the real device
  model driving the transport; `errors.py` converts failures into the `Error`
  envelope.
- **`client/`** — `link.py` is the seam client-side: build model →
  `model_dump(mode="json")` → call server entry point → parse reply → map
  `error_type` to an exception. `controller.py` holds the module-level
  `open_device` function and the `Controller` proxy it constructs;
  `channel.py` is the thin `Channel` proxy; `types.py` re-exports contract
  shapes; `errors.py` holds the exception hierarchy.

The client never imports server classes; it reaches the server only through
the one backend binding inside `link`. That keeps the seam a real boundary.

## 3. The public API surface

Fixed by `examples/normal_mode_timed_on.py` (the acceptance example) and the
polished naming from the contract branch's API skeleton. For the slice:

```python
from mightex_slc import OperatingMode, open_device

PORT: str | None = None  # e.g. "/dev/cu.usbserial-A6002xyz"; None = backend default

with open_device(port=PORT) as controller:        # -> Controller (context manager)
    if controller.requires_initialization:        # capability cached from open
        controller.initialize()
    channel = controller.channel(1)               # one-based; pure client-side accessor
    channel.configure_normal(current_max_ma=200.0, current_set_ma=100.0)
    channel.set_active_mode(OperatingMode.NORMAL)  # light on
    try:
        time.sleep(5.0)                           # timed-on is host-timed (no device primitive)
    finally:
        channel.set_active_mode(OperatingMode.DISABLE)  # light off
# context exit closes the device
```

Decisions this implies (resolving stale skeleton docstrings):

- `open_device` targets a serial port; there is no enumeration and no port
  scanning. Probing a port is a side-effecting act (opening sends ECHOOFF,
  which enters PC Mode on MA/CA-MU variants), so the user names the port —
  `None` means the backend's configured default target (the fake's one
  simulated controller; a future rs232 default set by constructor, env, or
  config). An rs232 backend without a configured default fails the open.
- `Controller` caches the `ControllerCapabilities` returned by open —
  `requires_initialization` must answer without a round trip. (The skeleton
  docstring's "holds a device_id and nothing else" is superseded.)
- `channel(n)` never crosses the seam; it just constructs a `Channel` proxy
  holding `(device_id, n)`.
- `configure_normal` takes flat `current_max_ma` / `current_set_ma` floats in
  mA; the device's per-family resolution rounding happens server-side.
- `OperatingMode` is an `IntEnum` with the device's own codes: DISABLE=0,
  NORMAL=1, STROBE=2, TRIGGER=3. These serialize as plain ints on the wire
  (`{"device_id": …, "channel": 1, "mode": 1}`).

## 4. Error model

Public hierarchy (client-side, carried unchanged from the contract branch):

```
MightexLEDError
├── DeviceConnectionError
│   └── DeviceNotFoundError
├── DeviceCommandError        (carries optional device `code`)
├── UnsupportedOperationError
└── ControllerClosedError
```

Plus plain `ValueError` for argument validation. The contract's `ErrorType`
enum holds exactly these six leaf names as strings, so `link` maps an error
reply back to the right exception class mechanically.

Errors surface in three distinct places:

1. **Client-side at request construction** — invalid arguments (set > max,
   negative current, channel < 1) fail Pydantic validation in `link` before
   anything crosses the seam.
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
semantics in `device_and_protocol.md` §7:

- One controller with a module family, ≥1 channels, a current resolution, and
  per-channel state: active mode, stored NORMAL `Imax`/`Iset`.
- `configure_normal` stores parameters **without changing output**;
  `set_active_mode` is what "lights the LED" (mutates active mode).
- Reports capabilities on open; `requires_initialization=True` so the
  example's `initialize()` branch actually executes in integration runs.

The acceptance run checks the fake's end state (stored params match, mode is
DISABLE after the `finally`), which is how the slice proves device semantics
without hardware.

## 6. The RS232 backend (future — design is settled, timing is not)

Out of scope for the current slice, but its shape is already known because the
test project proved it against real hardware. When it's built:

**Division of labor** (mirrors the test project's proven three-layer split):

- `transport/rs232/rs232_transport.py` — owns the pyserial port, framing, and
  timing. Knows bytes, not meaning.
- `transport/rs232/codec.py` — pure functions: build command strings
  (`"NORMAL 1 200 100"`), parse/validate responses. Knows meaning, not I/O.
  Keeping the codec pure is what made the old stack testable against a
  ~70-line fake serial object; preserve that property.

**The proven serial recipe** (details and provenance in
`device_and_protocol.md` §§2–5, 9):

```
open: 9600 8N1, no flow control, timeout 1.0 s
      send ECHOOFF, consume the response, do NOT require an ack
per command:
      reset_input_buffer()
      write(ascii + b"\n\r"); flush()
      read_until(b"\r"); sleep(0.02); read(in_waiting)   # drain
      decode ascii (errors="replace"); strip()
      empty -> timeout error
acks: "##" substring = ok; "#!"/"#?" prefix = device error; "is not defined" = unknown
parsers: strip "#", split on whitespace; ?CURRENT takes the LAST two tokens
```

Plus the behavioral obligations: ~0.3 s settle between a parameter write and
its read-back; disable channels in `finally` (the device keeps driving LEDs
after the port closes); program → verify → only then `STORE`; identifying the
right `/dev/cu.usbserial-*` path on macOS is on the user (the library never
scans for it), and running there is new ground.

**Known weak spots to do better than the test project:** the 20 ms drain is a
heuristic, not a framing guarantee (the per-command buffer reset is the real
safety net); the 0.3 s settle lived only in a test, unencoded; query-response
parsing (`?TRIGGER`/`?TRIGP`) was never made robust; no thread safety, no
retries. (Its lack of port auto-discovery is not a weak spot — that is now
this library's deliberate design; see §7.)

## 7. Deliberate cuts (settled — do not reopen)

- **No message broker, no sockets, no daemon — yet.** Single producer, single
  consumer, in-process. The single-owner-serial-port problem is real but
  deferred; the seam design makes the eventual daemon a wiring change.
- **No C++/vendor-DLL binding.** The SDK confirms its `SendCommand` passthrough
  uses the identical ASCII command set, so raw serial loses nothing.
- **No second validation layer.** Pydantic models are the only validator at
  the seam; hand-written jsonschema checks would drift.
- **No schema-artifact ecosystem.** `schemas/` YAML is generated documentation,
  kept current by rerunning the generator — nothing more. No consumers, no post-hoc refactoring
  projects, no audits of generated output (see `lineage.md` for the cautionary
  tale). The generator itself cross-references shared shapes instead of
  inlining copies — an implementation detail of the generator, not an
  ecosystem.
- **No HID/USB path, ever.** By decision the library interfaces over
  RS232/serial only (`device_and_protocol.md` §2). Units without an RS232
  path are out of scope — a procurement constraint, not a software one.
- **No port scanning or probing, ever.** No `enumerate_devices()`, no
  `list_serial_ports()`, no `probe_serial_ports()`. The vendor's
  `InitDevices`/`OpenDevice(DeviceIndex)` flow is USB/HID-only; RS232 users
  address the port directly. Probing is not passive — opening a port sends
  ECHOOFF, which enters PC Mode on MA/CA-MU variants — so the library opens
  exactly the port it is given and nothing else.
