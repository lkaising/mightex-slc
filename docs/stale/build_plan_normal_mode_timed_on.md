# Slice Build Plan: `normal_mode_timed_on`

Status: canonical working plan as of 2026-07-04. This is the corrected edition
of `~/Downloads/slice_build_plan_normal_mode_timed_on.md`, which it supersedes.
The plan takes the project from its current skeleton state (files exist,
headers only, no bodies) to a running implementation where
`examples/normal_mode_timed_on.py` executes end to end against the fake
transport with no hardware attached.

Corrections from the draft, in one place (details inline below):

- The draft assumed contract files had already been "ported" and needed import
  fixes. **Nothing has been ported.** The porting source is the abandoned
  contract branch at `~/Developer/Projects/mightex-slc` — its
  `contract/mightex_contract/` package is complete and is the reference for
  Phase 1.
- The draft said to "confirm `pyproject.toml` declares the src/ layout".
  **`pyproject.toml` was a 0-byte file** — Phase 0 authored it from scratch.
- The draft said to update the schema generator's imports and output path.
  **`scripts/generate_schemas.py` is a header-only stub** — it must be written,
  using the contract branch's working `contract/generate_schemas.py` as the
  reference.
- The "staleness check" the draft says to confirm **does not exist anywhere**
  and never did. Schema drift is covered by the working discipline of rerunning
  `scripts/generate_schemas.py` after any contract-model change (its built-in
  consistency check runs on every generation).
- The §11 open decision on `close_device.py`'s shape is **resolved**: the
  contract-branch file follows the uniform Request/Ok/Reply pattern, as hoped.
- Wire enum values are now pinned by three independent sources (vendor docs,
  hardware, contract branch): `OperatingMode` DISABLE=0 / NORMAL=1 / STROBE=2 /
  TRIGGER=3, serialized as plain ints.

Scope discipline is the point of this slice. Everything below builds the
smallest complete vertical that proves the architecture, and leaves every
out-of-scope operation dormant rather than half-built.

---

## 1. The goal, stated as an acceptance condition

The slice is done when this runs to completion, with no hardware, no leaked
exception, and the fake device left in the expected end state:

```
python examples/normal_mode_timed_on.py   # resolves mightex_slc from an editable install
```

The example (at `~/Developer/Projects/mightex/examples/normal_mode_timed_on.py`,
already fully written — the one complete file in the project) exercises exactly
this call sequence, and nothing else:

1. `open_device(port=PORT)` returns a `Controller` usable as a context
   manager (`PORT` is `None` for the backend's configured default target —
   the fake's one simulated controller — or a serial device path).
2. `controller.requires_initialization` is read; if true, `controller.initialize()`.
3. `controller.channel(1)` returns a `Channel`.
4. `channel.configure_normal(current_max_ma, current_set_ma)`.
5. `channel.set_active_mode(OperatingMode.NORMAL)`.
6. host-side `time.sleep(...)`.
7. `channel.set_active_mode(OperatingMode.DISABLE)` in a `finally`.
8. context exit calls `controller.close()`.

If those eight steps pass through the full stack and return correctly, the seam
is proven and the rest of the library is a matter of repeating the pattern.

---

## 2. Current state, and the gaps to close first

What exists: the `src/mightex_slc/` package tree is laid out across `client`,
`contract`, `server`, and `transport`, plus `scripts/generate_schemas.py`,
and `schemas/`. Every file carries a header; client/server/transport
files also carry intent docstrings. **No file contains executable code.**

Five gaps stood between the original skeleton and the full slice. **They were
never all Phase 0 tasks** — each gap below names the phase that owns it.
Phase 0 (complete; see `phase_status.md`) closed the packaging and
package-root items; the contract and schema items remain open for Phase 1:

- **`pyproject.toml` was empty (0 bytes) and had to be authored** — closed in
  Phase 0, as decided: **Hatchling** is the build backend, and the file
  declares the project name, the `pydantic` dependency, a `dev` extra
  (`ruff`, and `pyyaml` for the generator), and the `src/` layout so an
  editable install finds `mightex_slc`. The
  baseline workflow is plain pip in a standard environment —
  `python -m pip install -e ".[dev]"` — portable between pyenv-virtualenv on
  macOS and a plain `venv` on the eventual Ubuntu hardware machine. uv may be
  layered on as a personal convenience but is never required, and
  `.python-version` keeps its pyenv meaning (it names the virtualenv
  `mightex-slc`, not a Python version).
- **No top-level `mightex_slc/__init__.py` existed.** The example imports
  `from mightex_slc import OperatingMode, open_device`, so
  the package root must eventually assemble and re-export the public surface.
  Phase 0 created it as a header-only stub so the package is importable; the
  actual re-exports wait for Phase 5.
- **The contract models must be ported from the contract branch** (Phase 1).
  Source:
  `~/Developer/Projects/mightex-slc/contract/mightex_contract/` (complete,
  18 operations, 13 components — take only the slice subset in §5). Those files
  import `from mightex_contract...`; rewrite every intra-contract import as a
  relative import (`from ..base import ContractModel`), which survives future
  renames.
- **The schema generator must be written** (Phase 1, along with running it).
  Reference implementation:
  `~/Developer/Projects/mightex-slc/contract/generate_schemas.py` (complete and
  working — field-title suppression, one-line descriptions, deterministic YAML,
  generated-file headers). The new one lives at `scripts/generate_schemas.py`
  (outside `src/`, correctly out of the shipped wheel), covers only the slice's
  models, writes to the top-level `schemas/`, and stamps the new path in its
  headers. Keeping `schemas/` current is a working discipline: rerun the
  generator after any contract-model change.
- **The example lives outside the project** (`mightex/examples/`, a sibling of
  `mightex-slc/`). Running it requires the package installed editable
  (`python -m pip install -e ".[dev]"` from inside `mightex-slc/`). A standing
  constraint on how the slice is run, not a task in any phase.

---

## 3. Guiding principles for this slice

**Tracer bullet before breadth.** Build one operation (`open_device`) all
the way through every layer and get a green round-trip run before writing the
other four. This front-loads the seam risk and turns the remaining operations
into mechanical repetition of a known-good shape.

**Contract is upstream; build downstream from it.** The client and server both
import contract models. Writing either against types that do not yet exist
forces mirroring or comment-and-forget, the exact failure the reorg was meant
to kill. The contract lands first.

**Fake only.** The entire slice runs against `transport/fake`. The `rs232`
backend and its codec stay empty. (When rs232's turn comes, its design is
already settled — `architecture.md` §6.)

**Honor the serialize-and-validate seam even in-process.** The client builds a
Pydantic request model, dumps it with `model_dump(mode="json")` to a plain
dict, and hands that dict to the server, which reconstructs and validates the
matching model. Keep this even though everything is one process for now. It is
what makes a later socket or daemon a wiring change rather than a contract
change.

**Leave dormant code dormant.** Files for out-of-scope operations and
components stay empty. Do not stub them to silence a linter. An empty file with
a header is honest; a fake stub is a future reconciliation you will forget.
(Corollary: the skeleton's docstrings describe the *full* library — strobe,
trigger, fan, store. Ignore the out-of-scope parts; only the slice subset gets
bodies.)

---

## 4. Dependency map

Build order follows the arrows, from the thing that depends on nothing to the
thing that depends on everything.

```
contract/           depends on nothing (pure models)
   ▲
transport/base      the interface the server drives
   ▲
transport/fake      in-memory device, implements the interface
   ▲
server/             owns sessions + impl, validates with contract, drives transport
   ▲
client/             builds contract requests, calls server, parses replies
   ▲
mightex_slc/__init__  assembles the public surface the example imports
```

The client never imports the server's classes directly; it talks to the server
through a single in-process entry point (the backend binding in section 8).
That keeps the seam a real boundary you can later replace.

---

## 5. Scope: in and out

### In scope (the five operations)

| Operation | Why the slice needs it |
|---|---|
| `open_device` | step 1, the tracer bullet; establishes the `device_id` and session entry |
| `initialize` | step 2, exercised when the fake reports `requires_initialization` |
| `configure_normal` | step 4 |
| `set_active_mode` | steps 5 and 7 |
| `close_device` | step 8 |

### In scope (the five components + two bases)

`error`, `error_type`, `module_type`, `operating_mode`,
`controller_capabilities`; plus `contract/base.py` (`ContractModel`) and
`contract/operations/base.py` (`DeviceRequest`, `ChannelRequest`).

### Explicitly out of scope

- Every other operation: `configure_strobe`, `configure_trigger`,
  `set_normal_current`, `get_active_mode`, `read_parameters`,
  `read_load_voltage`, `store_settings`, `restore_factory_defaults`,
  `soft_reset`, `set_fan_pwm_level`, `device_info`, and the standalone
  `get_capabilities` (open already returns capabilities). These exist on the
  contract branch; do not port them.
- Components reachable only through those: `normal_parameters` (read-path only,
  reached through the contract branch's `ChannelState`), `strobe_parameters`,
  `trigger_parameters`, `trigger_polarity`, `channel_state`, `device_info`,
  `profile`, and `constants.py` (`REPEAT_FOREVER` is strobe-only).
- The `rs232` transport and codec.
- The single-owner daemon or socket (the deferred concurrency fix).
- Persistence to non-volatile memory.

A sanity check, now **confirmed against the contract branch**: its
`ConfigureNormalRequest` inlines `current_max_ma` and `current_set_ma` as flat
fields (with a `current_set_ma <= current_max_ma` model validator) and does not
reference `NormalParameters` — so the normal-mode slice does not pull in the
normal-parameters component. Correct, not an omission. Whether that split
should be kept for this library is a recorded Phase 1 investigation item
(see §6, Phase 1).

---

## 6. The build plan, phase by phase

### Phase 0: prep (no bodies yet) — complete 2026-07-04

Packaging, package root, and docs tracking — nothing else. Done:

- Authored `pyproject.toml`, applying the decisions recorded in section 11
  (Hatchling, `src/` layout, `pydantic` dependency, `dev` extra, pip-baseline
  workflow, Python `>=3.11`).
- Created the top-level `src/mightex_slc/__init__.py` as a header-only stub,
  so an editable install can import the package. No public re-exports yet —
  those are Phase 5.
- Added `docs/phase_status.md`, a lightweight per-phase progress ledger.

The other §2 gaps — contract model porting, the schema generator, and
generating the schemas — are **Phase 1 work**, not Phase 0.
`normal_parameters.py` is a header-only stub — leave it empty; that satisfies
"the contract tree matches the slice's real import closure."

Gate: **passed.** An editable install run from the sibling `examples/`
environment succeeded, `import mightex_slc` resolved to
`src/mightex_slc/__init__.py`, and package metadata reported `0.0.0` (details
in `phase_status.md`).

### Phase 1: contract foundation

Port the five operations, five components, and two bases from the contract
branch (`~/Developer/Projects/mightex-slc/contract/mightex_contract/`). Fix
every import to relative form. Write the three contract `__init__.py` files to
re-export **only what is present** — the contract branch's versions re-export
all 18 operations (its `operations/__init__.py` is 175 lines); copying them
verbatim is the single most likely first-import failure.

Then write `scripts/generate_schemas.py` (reference: the branch's working
generator) and generate the slice's schemas into `schemas/`. Doing this now
locks the contract shape before anything is built on top of it. From here on,
rerun the generator after any contract-model change so `schemas/` never
drifts.

Phase 1 investigation item (recorded, deliberately unresolved): the contract
branch keeps `NormalParameters` read-path only (reached through its
`ChannelState`), and its `ConfigureNormalRequest` inlines `current_max_ma` /
`current_set_ma` as flat fields (see the §5 sanity check). Decide during the
port whether that split stands for this library, or whether the
`configure_normal` contract should reuse or bake in the `NormalParameters`
shape. Until decided, `normal_parameters.py` stays an empty stub.

Gate to pass before moving on: `import mightex_slc.contract` succeeds; a valid
request model for each of the five operations constructs, dumps to JSON, and
re-validates; an invalid one is rejected. Concrete invalid cases worth
checking: `configure_normal` with `current_set_ma` above `current_max_ma`, a
negative current, a channel number below one, and a missing `device_id`. This
is a pure-contract checkpoint with no transport, server, or client in the
picture, verified by a throwaway script or REPL session.

### Phase 2: transport seam and fake

Define `transport/base.py` as the interface the server drives: open the
controller at a serial-port target (returning a handle and its capabilities),
issue a per-channel or per-device command, and close a handle. Keep it small;
it only needs to carry the five operations of this slice, and it is allowed to
grow later without the contract moving.

Implement `transport/fake/fake_transport.py` as an in-memory device per
`architecture.md` §5: one fake controller with a module family, a channel
count of at least one, a current resolution, and per-channel state (active
mode, stored normal max and set). It accepts `initialize`, `configure_normal`,
and `set_active_mode` by mutating that state, and reports capabilities on
open with `requires_initialization=True`, so the acceptance run exercises the
`initialize()` branch. Its semantics — configure stores but does not emit; only
`set_active_mode` changes output — are the device's real semantics
(`device_and_protocol.md` §7), not conveniences.

### Phase 3: tracer bullet, `open_device` end to end

Wire the thinnest possible full path for one operation and get it green:

client-level open builds `OpenDeviceRequest`, dumps it, and calls the server
entry point; the server validates, routes to a handler, opens the fake
transport, creates a live handle, registers it under a new `device_id`, and
returns `OpenDeviceOk` with that id, the serial number, and the capabilities;
the client parses the reply.

`open_device` is deliberately first because it is the operation that
establishes the session: it proves the seam mechanics (model build, JSON dump,
dispatch, validate, route, transport call, reply model, parse) **and** the
`device_id` registration every later operation depends on, while needing no
channel and no pre-existing `device_id` — still the smallest self-standing
round trip. Everything after this is repetition.

Prove it with a throwaway script (or REPL session) that calls the client-level
open path with no arguments and confirms that, through the full seam, the fake
answers with an `OpenDeviceOk` carrying a non-empty `device_id`, serial
`04-000000-001`, and capabilities with `requires_initialization=True`. (Close
is not part of the tracer; the throwaway process exiting is fine.)

### Phase 4: fan out the remaining four operations

Following the proven path, add handlers for `initialize`, `configure_normal`,
`set_active_mode`, and `close_device`. Every one of them carries the
`device_id` from open, and the server looks up the live handle by it.
`close_device` removes it from the session.

Gate to pass: each of the five operations round-trips against the fake in
isolation. No public proxy layer is required yet; these can be driven directly
through `link` in a throwaway script.

### Phase 5: public surface

Now add the ergonomic layer the example actually calls:

- `client/errors.py`: the public exception hierarchy (`architecture.md` §4).
- `client/types.py`: re-export `OperatingMode`, `ModuleType`,
  `ControllerCapabilities` from the contract (imported, not mirrored).
- `client/controller.py`: the module-level `open_device(port=None)` function
  alongside the `Controller` proxy it constructs (the `open()`-returns-object
  idiom; with enumeration gone there is nothing else a discovery module would
  hold). The `Controller` holds `device_id` **and the capabilities from open**
  (its skeleton docstring saying "a device_id and nothing else" is superseded —
  `requires_initialization` must answer without a round trip), with
  `requires_initialization`, `initialize`, `channel`, `close`, `is_closed`,
  and the context-manager methods.
- `client/channel.py`: the `Channel` proxy holding `device_id` and a one-based
  channel number, with `configure_normal`, `set_active_mode`, and `number`.
  `channel(n)` is a pure client-side accessor that builds this proxy; it never
  crosses the seam.
- `mightex_slc/__init__.py`: re-export `open_device`, `Controller`, `Channel`,
  `OperatingMode`, and the exception classes.

### Phase 6: acceptance — run the example

Run `examples/normal_mode_timed_on.py` against the editable install and
confirm it completes cleanly: no leaked exception, and the fake left in the
expected end state (the channel's stored normal params match what was set,
and the active mode is `DISABLE` after the `finally`).

Also confirm one error path by hand (throwaway script or REPL): a second
`open_device()` while the controller is held open raises
`DeviceConnectionError` (the fake's `TransportError` mapped through the
`Error` envelope). This proves the error-reply mapping in `link`, which the
happy-path example never exercises. (`DeviceNotFoundError` — nothing answers
at the port — is reachable only on the rs232 backend and waits for hardware
bring-up; the fake cannot produce it.)

---

## 7. File-by-file responsibilities for the slice

Contract (port from the contract branch, fix imports, trim re-exports):

- `contract/base.py`: `ContractModel`, the frozen base with extra fields
  forbidden.
- `contract/operations/base.py`: `DeviceRequest` (adds `device_id`),
  `ChannelRequest` (adds `device_id` and one-based `channel`).
- `contract/components/error.py`: the `Error` reply envelope shared by every
  operation (with the code-only-for-DeviceCommandError validator).
- `contract/components/error_type.py`: `ErrorType`, the enum of exception
  names the client maps a reply back onto.
- `contract/components/module_type.py`: `ModuleType`, the device's own family
  numbering (AA=0 … QA=12 — load-bearing, never renumber).
- `contract/components/operating_mode.py`: `OperatingMode` (IntEnum,
  DISABLE=0, NORMAL=1, STROBE=2, TRIGGER=3 — device codes).
- `contract/components/controller_capabilities.py`: `ControllerCapabilities`,
  the open-reply payload where `requires_initialization` lives.
- `contract/operations/{open_device, initialize, configure_normal,
  set_active_mode, close_device}.py`: request and reply models, one file per
  operation, uniform `<Op>Request` / `<Op>Ok` / `<Op>Reply` (discriminated on
  `status`) pattern. `open_device` takes a serial target
  (`port: str | None`), not a discovery index.

Transport:

- `transport/base.py`: the interface the server drives.
- `transport/fake/fake_transport.py`: in-memory device with per-channel state.

Server:

- `server/session.py`: registry mapping `device_id` to a live device handle.
- `server/impl/controller.py`: device-side controller model (open, initialize,
  capabilities, channel access, close), driving the transport.
- `server/impl/channel.py`: device-side channel logic for `configure_normal`
  and `set_active_mode`.
- `server/dispatch.py`: validate an incoming payload with the matching request
  model, route by operation name to a handler.
- `server/api.py`: the in-process entry point the client calls; owns dispatch,
  session, and the transport binding.
- `server/errors.py`: translate an execution failure into an `Error` reply and
  choose its `error_type`.

Client:

- `client/errors.py`: `MightexLEDError` and its subtypes.
- `client/types.py`: re-exports of the contract enums and shapes.
- `client/link.py`: build request model, dump, call the server entry point,
  parse the reply, and on an error reply map `error_type` to the exception to
  raise. Also owns the default backend binding and its narrow injection point
  (section 8).
- `client/controller.py`: the module-level `open_device` function and the
  `Controller` proxy it constructs.
- `client/channel.py`: `Channel` proxy.
- `mightex_slc/__init__.py`: the assembled public surface.

---

## 8. The in-process wiring (the backend binding)

This is the piece most easily hand-waved, so it gets its own section. The
question it answers: how does `open_device()`, a module-level function with no
`device_id` yet, reach the server and the fake transport?

For the slice, bind a single in-process server, itself bound to the fake
transport, and give the client `link` a reference to it. The simplest honest
form is a default backend that `link` calls, constructed once as an in-process
server over the fake transport. `open_device()` then flows as
`link.call("open_device", {"port": None})` into that server, which opens the
fake and returns the reply.

Keep this binding behind one seam so the later swap is a wiring change only.
Nothing in the contract or the client proxies should know whether the backend
is an in-process server over a fake, an in-process server over rs232, or a
socket to a daemon. When rs232 arrives, only the transport the server is bound
to changes.

Backend injection (decided): `link` creates the default backend lazily on
first use and exposes one narrow injection/reset point that replaces it (e.g.
`link.use_backend(...)`). That is the whole mechanism — no special-case
branching in production code. It is the same seam through which the rs232
backend (or a socket to a daemon) is later installed, so it earns its place
regardless of how the slice is verified.

---

## 9. Data flow for one operation

Concrete trace of `channel.set_active_mode(OperatingMode.NORMAL)`, which is
the representative shape every channel operation follows:

1. User calls `channel.set_active_mode(OperatingMode.NORMAL)`.
2. The `Channel` proxy asks `link` to run `set_active_mode` with its
   `device_id`, its channel number, and the mode.
3. `link` builds `SetActiveModeRequest(device_id=..., channel=1, mode=NORMAL)`.
   Any argument-level validation fires here, client-side, at model
   construction.
4. `link` serializes it: `request.model_dump(mode="json")` gives
   `{"device_id": "...", "channel": 1, "mode": 1}`.
5. `link` calls the server entry point with the operation name and that dict.
6. `server/dispatch.py` reconstructs `SetActiveModeRequest(**payload)`, which
   re-validates as the trust boundary, and routes to the handler.
7. The handler looks up the live device in `session` by `device_id`.
8. The handler calls `impl/channel` to set the active mode, which drives the
   fake transport and mutates its state.
9. The handler returns `SetActiveModeOk()`, serialized to `{"status": "ok"}`.
10. `link` parses the reply; status is ok, so it returns success (here,
    `None`).

On failure, the handler returns an `Error` reply carrying `error_type`,
`message`, and, for a `DeviceCommandError`, `code`. `link` reads `error_type`
and raises the matching exception in the user's process.

---

## 10. Where errors surface

Three distinct places, worth keeping straight:

- **Client-side, at request construction.** Invalid arguments (set above max,
  a negative current, a bad channel) raise `ValueError` when `link` builds the
  request model, before anything crosses the seam. The cross-field rule in
  `ConfigureNormalRequest` is one of these.
- **Server-side, at re-validation.** `dispatch` reconstructs the model as a
  trust boundary. In-process with a well-behaved client this rarely fires, but
  it is the reason a future untrusted caller cannot bypass the contract.
- **Device or execution failures.** These come back as an `Error` reply.
  `link` maps `error_type` to the exception class. An unanswering serial port
  becomes `DeviceNotFoundError` (rs232 only — the fake cannot produce it); use
  of a `device_id` the session does not know becomes `ControllerClosedError`.

---

## 11. Decisions

Resolved (previously open in the draft):

- **`close_device.py` shape** — confirmed on the contract branch: uniform
  pattern, `CloseDeviceRequest(DeviceRequest)` plus `CloseDeviceOk`, no new
  components. The component closure does not grow.
- **`normal_parameters.py`** — already a header-only stub; leave it empty for
  Phase 0. Whether it stays read-path only or informs the `configure_normal`
  contract is the open Phase 1 investigation below.
- **Intra-package imports** — relative imports throughout, decided.
- **Schema generation timing** — Phase 1, decided.
- **Controller state** — caches capabilities from open (see Phase 5).
- **Wire enum values** — device integer codes, serialize as ints, pinned.

Resolved 2026-07-04 (the former Phase 0 decisions):

- **Build backend and workflow** — Hatchling as the build backend; the
  baseline workflow is plain pip in a standard environment
  (`python -m pip install -e ".[dev]"`), portable between pyenv-virtualenv on
  macOS and a plain `venv` on the eventual Ubuntu hardware machine. uv stays
  optional, never required; `.python-version` keeps its pyenv meaning.
- **Fake `requires_initialization`** — `True`, so the acceptance run exercises
  `initialize()`. Not configurable until something actually needs a `False`
  device.
- **Home for `open_device`** — a module-level function in
  `client/controller.py`, alongside the `Controller` it constructs; no
  discovery module exists. (Superseded 2026-07-06: the original decision
  placed `enumerate_devices` and `open_device` in a `client/discovery.py`,
  but enumeration was removed when the API went serial-target-first.)
- **Backend injection point** — a narrow injection/reset point in
  `client/link.py` over a lazily-created default backend (section 8); the same
  seam later carries the rs232 rebinding. No special-case branching.
- **Python floor** — `requires-python = ">=3.11"`, set in Phase 0. The active
  pyenv virtualenv and the verified examples environment both run Python
  3.11.13; no older interpreter is in the picture.

One item is deliberately left open, scheduled as a Phase 1 investigation (see
§6, Phase 1): whether `NormalParameters` remains read-path only, as on the
contract branch, or whether the `configure_normal` contract should reuse or
bake in that shape. No other open decisions remain.

---

## 12. What this slice sets up

When it is green, the architecture is proven on a real path, and the remaining
work is additive rather than structural. Adding an operation later means one
contract operation file, one handler, one bit of fake behavior, and one proxy
method, following the shape this slice establishes. Swapping the fake for
rs232 means implementing `transport/rs232` against the same `transport/base`
interface and rebinding the server, with the contract and the client untouched
— and the rs232 design is already settled by hardware-proven evidence
(`architecture.md` §6, `device_and_protocol.md` §9). Neither of those disturbs
anything built here, which is the signal that the slice was scoped correctly.
