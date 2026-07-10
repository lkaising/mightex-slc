# RS232 Backend Handoff — normal-mode slice, to real hardware

> **Outcome (2026-07-06): executed.** The RS232 backend is built
> (`transport/rs232/codec.py` + `rs232_transport.py`) and hardware-verified on
> the bench SLC-SA04-U/S — an LED was driven on and off through the public
> API. Backend selection is `transport.create_transport()`
> (`MIGHTEX_SLC_BACKEND`, default `rs232`; `MIGHTEX_SLC_PORT`); `initialize`
> was removed as an operation (ECHOOFF folded into `open_device`, and
> `requires_initialization` left the capabilities); `server/impl/` is filled
> in and dispatch routes through it; tests and bring-up probes live under
> `../../../examples/`. Device behavior observed at bring-up that differs
> from the record below is logged in
> [`../reference/device_and_protocol.md`](../reference/device_and_protocol.md)
> §§5–6, 9 (12-field `?CURRENT`, clean `##` from ECHOOFF, bare DEVICEINFO
> framing). §3's "pyserial not installed" and parts of §9's housekeeping list
> are superseded.

> **Update (2026-07-10):** the backend was since reorganized into four modules
> (`codec.py`, `capabilities.py`, `serial_link.py`, `rs232_transport.py`) with
> no behavior change; file references below reflect the original two-file
> layout.

Status: written 2026-07-06 on the Linux hardware machine, from a fresh audit of
the live code, the two projects, and the connected device. This is a **map, not
a manual**: it points at where the truth lives and flags what to trust. It does
**not** tell you how to implement anything — no build order, no function
bodies, no resolutions of the open design questions. Those are your job (and the
job of the prompt that dispatches you).

---

## 1. The mission

Bring the **`normal_mode_timed_on` slice to a genuinely good, hardware-real
state on this machine.** Centrally that means building the real RS232 transport
backend — the two empty stub files under `src/mightex_slc/transport/rs232/` — so
the library drives the *actual* Mightex controller wired to the bench, and then
proving the existing public API does so cleanly. Secondarily it means closing
the small housekeeping gaps that keep the project from being in a good state
(see §9).

**Scope stays the turn-on-normal slice.** In: `open_device`, `initialize`,
`configure_normal`, `set_active_mode`, `close_device`, over NORMAL mode only.
Out, by standing decision (do not widen the slice): strobe, trigger, fan, store,
new operations, the single-owner-port daemon. See the deliberate cuts in
[`../reference/architecture.md`](../reference/architecture.md) §7.

The seam this plugs into is already built and proven against an in-memory fake —
the whole client→server→transport stack runs end-to-end today. Your work is to
add a second transport behind the existing interface, not to touch anything
above it.

---

## 2. Read this in order

| # | Source | Why | Trust |
|---|---|---|---|
| 1 | This doc | The map | — |
| 2 | The live code under `src/mightex_slc/` | Ground truth of what exists | **ground truth** |
| 3 | [`../vendor/`](../vendor/) | The wire protocol | **authoritative** |
| 4 | The old test project (§7) | Hardware-proven reference to port *from* | proven-but-old |
| 5 | [`../reference/`](../reference/) | Design + protocol digest | mostly-current, **verify** |
| 6 | [`../stale/`](../stale/) | History + ideas | **do not trust literally** |

The three tiers matter. Read §6 (trust tiers) before you rely on any doc.

---

## 3. You are on the hardware machine — the concrete facts

This box is **Linux**, and the device is physically connected. (Every older doc
assumes macOS with `/dev/cu.usbserial-*` paths and a `~/Developer/Projects/...`
layout — all of that is stale; ignore it. The real project root is
`/home/labuser/Research/mightex/mightex-slc`.)

Confirmed on 2026-07-06:

- **`/dev/ttyUSB0`** — an **FTDI FT232R USB-UART** (`0403:6001`,
  `usb-FTDI_FT232R_USB_UART_AQ02KL9S`). This is the RS232 path to the LED
  controller (a DB9 through a USB-serial adapter — exactly the hookup the
  reference docs describe). **This is your target port.**
- **`/dev/ttyACM0`** — an **Arduino** (`www.arduino.cc`). This is the NIR
  frame-sync trigger box, **not** the controller. Do not open it.
- The user is in the **`dialout`** group, so serial access works without sudo.
- **`pyserial` is NOT installed** in the project venv (`.venv`), and is **not**
  declared in `pyproject.toml`. You will need to add it.
- **Which controller model is actually attached is unconfirmed.** The reference
  docs assume an **SLC-SA04-U/S** (firmware 3.1.8, serial `04-251013-011`,
  4-channel, 1 mA resolution, 1 A NORMAL ceiling), but they also anticipate
  MA04-MU/CA04-MU variants, which behave differently (mandatory PC-Mode entry,
  no trigger, different limits). **Confirm the real unit via `DEVICEINFO` before
  trusting any model-specific fact.** This is a verify-first item, not something
  to resolve from these docs.

---

## 4. The target: two empty stub files

Everything you build lands in these two files (both currently header +
docstring, zero code). Their own docstrings state the intended split — read
them first:

| File | Responsibility (per its docstring) |
|---|---|
| `src/mightex_slc/transport/rs232/codec.py` | **Pure wire format** — encode operations into the controller's ASCII command strings, decode/parse the responses. Knows meaning, not I/O. The only place the RS232 protocol lives. Keeping it pure (no serial port) is what makes it testable. |
| `src/mightex_slc/transport/rs232/rs232_transport.py` | **Real serial backend** over pyserial — owns the port, framing, timing; sends codec-built commands, reads/decodes replies. Knows bytes, not meaning. Also where the single-owner-port concern would be handled if it becomes real. |

This bytes/meaning split is deliberate and load-bearing — it mirrors the
hardware-proven old project (§7) and the design in
[`../reference/architecture.md`](../reference/architecture.md) §6. Preserve it.

---

## 5. The interface you must satisfy — and the one wiring point

The RS232 backend is an implementation of an interface that **already exists and
is fully specified**:

- **`src/mightex_slc/transport/base.py`** — `Transport` (ABC). Your backend
  subclasses this and implements the five slice operations: `open_device`,
  `initialize`, `configure_normal`, `set_active_mode`, `close_device`. Open
  returns a `TransportOpenResult(handle, serial_number, capabilities)`; failures
  raise the `TransportError` family (`DeviceNotPresentError`,
  `InvalidHandleError`, `CommandRejectedError`). Read this file in full — it is
  the contract, and its docstrings carry the behavioral obligations (opening is
  side-effecting; close is idempotent and never a safety action; etc.).
- **`src/mightex_slc/server/errors.py`** — already maps those transport
  exception types to the client-facing error envelope. Raise the existing
  exception types and correct error surfacing comes for free; you do not touch
  this file.

**The single wiring point.** The fake is bound in exactly one line:
`src/mightex_slc/client/link.py`, in `_default_backend`, which constructs
`Server(FakeTransport())`. That is the *only* place a concrete transport is
named. Going live means selecting the RS232 backend there instead (how that
selection is gated — argument, env, config — is a design choice for you, not a
decision this doc makes). Note `src/mightex_slc/transport/__init__.py`'s
docstring anticipates a small backend factory that **does not exist yet**.
Nothing above `transport/` — no contract, server, or client code — needs to
change.

For the exact top-to-bottom trace of how a call flows through the seam (link →
Server → dispatch → session → transport), see
[`../reference/architecture.md`](../reference/architecture.md) §2 and the data-flow
trace in [`../stale/build_plan_normal_mode_timed_on.md`](../stale/build_plan_normal_mode_timed_on.md)
§9 (stale doc — the *flow* is accurate, ignore its "not yet built" framing).

---

## 6. Trust tiers — where to look and how much to believe it

The `docs/` folder is now sorted by how much you can trust it. **When sources
disagree, the order is: real hardware > `vendor/` > the live code > `reference/`
> `stale/`.**

- **`../vendor/` — authoritative.** The two 2018 vendor documents (SDK
  Description v1.1.4 = the command set; User Manual v1.3.6 = modes, module
  matrix, limits, safety). The ultimate authority on the wire protocol. See §8
  for a routing map into them.
- **`../reference/` — mostly current, verify against code + hardware.**
  [`architecture.md`](../reference/architecture.md) (the design and the RS232
  recipe) and [`device_and_protocol.md`](../reference/device_and_protocol.md)
  (the consolidated hardware/protocol reference). Genuinely valuable, but they
  carry stale threads — see §10.
- **`../stale/` — history and ideas, do not trust literally.** Good thinking and
  hard-won history, but out of pace with the code. See §11.

Note: some cross-references *inside* the moved docs now point at old sibling
locations (they were written when everything sat flat in `docs/`). Treat those
internal links as approximate — this handoff doc is the current navigation hub.

---

## 7. The hardware-proven reference implementation (port *from*, don't import)

`/home/labuser/Research/mightex-slc-test` — the deprecated first project. It is
flat and superseded, but it is the **only code ever run against real hardware**,
and its three-layer split (bytes → meaning → API) is exactly the shape you are
rebuilding. Read it as the proven reference to translate, not a dependency to
import (its exception tree and flat API are superseded by the new layering).

| File | What to lift |
|---|---|
| `src/mightex_slc/transport.py` | The serial I/O layer — port config (8N1/9600), the `send` TX/RX cycle, and `_read_response`'s framing/drain. **Maps onto the new `rs232_transport.py`.** The single most valuable file. |
| `src/mightex_slc/protocol.py` | Command-string builders, ack/error checking (`_check_ack`/`_expect_ack`), and response parsers (`_parse_mode`, `_parse_normal_params`, `DeviceInfo.from_response`). **Maps onto the new `codec.py`.** |
| `src/mightex_slc/controller.py` | Two load-bearing *sequences* only: `connect()` (open → ECHOOFF) → your `initialize`; and the store-then-activate turn-on (`NORMAL …` then `MODE ch 1`) → your `configure_normal` + `set_active_mode`. |
| `src/mightex_slc/constants.py` | Limits/defaults reusable close to verbatim (channel range, current ceilings, baud, timeout). |
| `tests/conftest.py` | A `FakeSerial` byte-level test double — a ready template for testing the new backend without hardware. |
| `tests/test_controller.py` | `TestHardwareIntegration` (marked `@pytest.mark.hardware`, real `/dev/ttyUSB0`) records observed device behavior — including the post-write settle delay before a read-back. |
| `docs/command_reference.md` | The old project's own wire-protocol notes; cross-check against `vendor/`. |

**The proven serial recipe** — asymmetric terminators, per-command buffer
hygiene, the post-CR drain, substring/prefix ack rules, the `?CURRENT`
calibration-field trap, the post-write settle, and unacked ECHOOFF — is
described with provenance in
[`../reference/device_and_protocol.md`](../reference/device_and_protocol.md) §9
("the goldmine", 14 items) and §3–§6, and embodied concretely in the old
`transport.py` and `protocol.py`. **Read those for the actual values; this doc
deliberately does not restate them.**

**Do NOT carry over** (out of scope for the slice): all STROBE/TRIGGER code and
`trigger_programmer.py`; the old `MightexError` exception tree (translate to the
new `TransportError` family instead); the old flat `controller.py`/`get_controller`
API; `LoadVoltage`.

**Known weak spots the old code has — do better** (all detailed in the audit
material and visible in the source): ECHOOFF routed through a reply-demanding
`send` (brittle, echo-state-dependent); echo pollution not modeled; the 20 ms
post-CR drain (in the driver) and the 300 ms post-write settle (which lives only
in a hardware test, never encoded in the driver) are unexplained magic numbers;
the per-command `reset_input_buffer` (at the top of every send) discards
unsolicited data;
`_parse_normal_params` is positionally fragile and never applies the per-family
current-resolution scaling; `FakeSerial.reset_input_buffer` is a no-op so buffer
bugs pass silently; and there is no handle/ownership model (the new
`TransportHandle` / single-owner-port concern has no precedent here — build it
fresh).

---

## 8. The authoritative protocol source — `../vendor/`

Route all wire-protocol questions here. The markdown has no anchor IDs; navigate
by section heading. (Line numbers below are from the current files and are a
convenience, not a guarantee.)

- **SDK Description** (`../vendor/mightex_sirius_multi_channel_led_controller_sdk_description.md`)
  — the command set. Serial params + DB9 pinout, command format and the
  `<LF><CR>` terminator, echo modes / PC-Mode, response codes, and the per-mode
  command tables (MODE/?MODE, NORMAL/CURRENT/?CURRENT, STORE, DEVICEINFO) live in
  its "Command Sets" region.
- **User Manual** (`../vendor/mightex_sirius_multi_channel_led_controller_user_manual.md`)
  — the module-family feature matrix, electrical/current/power limits,
  per-family current resolution, operating-mode semantics, safety limits, the
  external-trigger circuit, and the MA04/CA04-MU PC-Mode/fan sections.

For the normal-mode slice specifically, the facts you need — 9600 8N1 serial
params, the `<LF><CR>` command terminator, ECHOOFF/PC-Mode, the `##`/`#!`/`#?`/
`#data`/`is not defined` response codes, `MODE`/`?MODE`, `NORMAL`/`CURRENT`/
`?CURRENT` (with its leading calibration fields), `DEVICEINFO`, `STORE`, and the
volatile-until-STORE + factory-default semantics — are all in the SDK's command
region, with module limits/resolution in the UM matrix.

**Vendor contradictions you must NOT resolve from memory** — resolve them
against hardware or by explicit decision, never by guessing:

1. STROBE repeat-count lower bound and off-by-one (SDK says 0-based +1; UM says
   1-based). *(Out of slice scope, but noted.)*
2. Profile step count per module ("2 vs 3 steps", which families). *(Out of scope.)*
3. MA/CA channel power limit stated as both **15 W and 18 W**, plus a
   Normal/Strobe table typo.
4. Generic "1000 mA NORMAL max" is not universal (HA/HV 2000, MA/CA 1200).
5. **`DEVICEINFO` grammar is under-specified** — only sample strings, differing
   between docs and the real unit (and even the vendor name differs). **Parse by
   keyword, never by position; confirm against hardware.**
6. Response line-ending byte order (`<CR><LF>` vs `<LF><CR>`, trailing space) is
   internally inconsistent — confirm empirically.

**What the vendor docs do NOT cover** (get from hardware): the `Error` command
referenced after `#!` (undocumented — no format, no code table); exact response
line-ending bytes; echo-pollution/whitespace tolerance; which arg ranges trigger
`#?` vs `#!`; response latency and how long `STORE`/`RESET` take before the port
is ready; and `CURRENT`'s response when the channel isn't in NORMAL mode.

---

## 9. Housekeeping gaps that also stand between here and "good state"

Not the RS232 backend itself, but part of the mission (§1). Ground-truthed from
the live code on 2026-07-06:

- **`pyserial`** is neither installed in `.venv` nor declared in
  `pyproject.toml` (whose only runtime dependency is `pydantic`; the `dev`
  extra adds `ruff` and `pyyaml`).
- **`README.md` at the project root is empty (0 bytes).**
- **`src/mightex_slc/server/impl/controller.py` and `channel.py` are empty
  stubs** — the "device model" layer the architecture describes was never built;
  `dispatch.py` drives the transport directly. This is a deliberate, working
  shortcut; decide whether the RS232 backend needs any server-side device logic
  to have a home, or whether direct-drive still suffices.
- **The phase ledger is wrong** (see §11) — don't let it convince you Phases 5/6
  are unbuilt; they are done.

---

## 10. `../reference/` — valuable, but verify these stale threads

Both docs are mostly current and worth reading in full, but carry known drift:

- **Paths and OS.** Both assume macOS and a `~/Developer/Projects/...` root, and
  `device_and_protocol.md` §1 explicitly (and now wrongly) calls the environment
  macOS with `/dev/cu.usbserial-*`. Reality is Linux / `/dev/ttyUSB0` / FT232R
  (§3 above). `device_and_protocol.md` §10 item #9 ("macOS serial untested") is
  now moot/inverted.
- **"Future" framing.** `architecture.md` §6 (and §2, §5) treats the RS232
  backend as future/out-of-scope work. That is exactly what you are now building
  — read §6 as your spec, not as a someday.
- **Hardware model.** The SA04 assumption (§10, §3 above) needs a `DEVICEINFO`
  confirmation.
- **Code-shape claims.** `architecture.md` §2 names specific files and a
  server-side `impl/` layer; verify against the tree (the `impl/` layer is empty
  — §9).

Still solid and worth pointing to: `architecture.md` §1 (vision + the two
working rules), §2 (five-layer design), §3 (public API), §4 (error model), §6
(the RS232 recipe and the three-layer split — reframed to "now"), §7 (deliberate
cuts); and `device_and_protocol.md` §3–§9, especially **§9's 14-item "goldmine"
of hardware-proven quirks** (the highest-value empirical content in the repo)
and §6's annotated command table.

**The provenance convention** — **[V]** vendor / **[HW]** hardware-verified /
**[C]** library convention — is worth preserving. `[HW]` items are battle-tested
and safe as-is; `[V]`-only items need hardware confirmation before you trust
them; and re-check any `[C]` tag, since several encode the old macOS assumption.

---

## 11. `../stale/` — history and ideas, do not trust literally

These captured the project's design thinking and build history in early July
2026 and have not kept pace with the code. **Every concrete claim in them is
suspect** — verify against `vendor/`, the live code, and real hardware before
relying on it.

- **`stale/phase_status.md`** — the ledger. **Known wrong:** it marks Phases 5
  (public surface) and 6 (acceptance) "not started," but both are done in code
  (the full public API is implemented and the example runs clean against the
  fake). Never read completion state from here — read it from the code. Its
  Phase 2–4 completion *notes* are still useful narrative of how the seam was
  built.
- **`stale/build_plan_normal_mode_timed_on.md`** — its opening premise ("no file
  contains executable code") is entirely obsolete, and it references six
  operations / `enumerate_devices` that were later cut to five. Still valuable
  for the **five guiding principles (§3)**, the dependency map (§4), the
  scope-in/out record (§5), the seam data-flow trace (§9), and the decisions
  record (§11).
- **`stale/lineage.md`** — mostly durable *history*: why the two predecessor
  projects were abandoned (the breadth-first cautionary tale that motivates the
  slice method), what was salvaged, the **cut list** ("do not reopen"), and the
  origin of the provenance rule (a draft was caught fabricating device facts).
  Its filesystem paths are all the stale `~/Developer` layout.
- **`stale/README.md`** — the old docs index; its "current state" section is
  fully obsolete (claims server/client/`__init__` are stubs — they are built).
  Good for the elevator pitch and the no-enumeration rationale.

Framing to carry forward: *good ideas and history, but reality wins — check
every concrete claim against the vendor docs, the actual code under
`src/mightex_slc/`, and real hardware.*

---

## 12. What this doc deliberately does NOT do

It does not give a build order, function-level guidance, or code. It does not
resolve the open design questions (backend selection/gating, how `initialize`
maps to ECHOOFF on this specific unit, current-resolution scaling, the
handle/ownership model, whether `server/impl/` gets filled). It points you at
the authoritative sources and the proven precedent; deciding and building from
them is your work.
