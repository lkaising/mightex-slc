# mightex-slc Documentation

Status: source of truth as of 2026-07-04. This folder supersedes every earlier
document, branch, and project. If something here conflicts with an older
artifact, this folder wins.

---

## What this project is

`mightex-slc` is a Python library for controlling Mightex Sirius SLC-series
multi-channel LED controllers. The library presents a clean, transport-neutral
public API (`enumerate_devices()`, `open_device()`, `Controller`, `Channel`),
validates every call at a contract seam built from shared Pydantic models, and
drives the device through a swappable transport layer — an in-memory fake for
hardware-free development, and an RS232 backend for real hardware.

Development is **slice-driven**: instead of building the whole library at once
(the mistake that killed the previous attempt), we build one narrow vertical
slice at a time, proving the full stack end to end before adding breadth. The
current slice is **`normal_mode_timed_on`**: enumerate, open, initialize,
configure a channel's NORMAL-mode current, switch the channel on, wait
host-side, switch it off, close — all against the fake transport, no hardware.

The acceptance example for the slice is the one fully-written file in the project:
`../../examples/normal_mode_timed_on.py`. It doubles as the de facto public API
specification.

## Current state (verified 2026-07-04, post-Phase 1)

Phase 1 (the contract foundation) is complete: `src/mightex_slc/contract/`
holds the slice's six operations, six components, and two base models as
working Pydantic code, and `scripts/generate_schemas.py` generates the YAML
schemas in `schemas/` (each shared shape is emitted once, in its component
file, and cross-referenced — not inlined per file; rerun the generator after
any contract-model change). Everything else under `src/` is still a
header-only or docstring-only stub, the root `README.md` is still empty, and
Phase 2 (the transport seam and fake) has not started. `phase_status.md` in
this folder tracks per-phase progress.

## The documents

Read in this order:

| Document | What it holds |
|---|---|
| [`architecture.md`](architecture.md) | The vision, the five-layer design, the public API surface, the error model, and the transport-layer design (including the hardware-proven RS232 recipe for when that backend is built). |
| [`device_and_protocol.md`](device_and_protocol.md) | The consolidated hardware reference: our bench hardware, serial parameters, command framing, the full RS232 command table, mode semantics, limits, and every quirk learned from the real device. |
| [`build_plan_normal_mode_timed_on.md`](build_plan_normal_mode_timed_on.md) | The corrected, canonical slice build plan. Supersedes the draft in `~/Downloads/slice_build_plan_normal_mode_timed_on.md`, whose stale references it fixes. |
| [`phase_status.md`](phase_status.md) | The lightweight progress ledger: one row per build-plan phase with its gate, status, and completion note. |
| [`lineage.md`](lineage.md) | Where everything came from: the two deprecated predecessors, why the contract branch was abandoned, what was salvaged, and what must not be resurrected. |
| [`vendor/`](vendor/) | The authoritative vendor documentation, converted to markdown: *SDK Description* v1.1.4 (the command set) and *User Manual* v1.3.6 (modes, module matrix, safety). |

## Provenance convention

Carried forward from the contract branch — its single best idea. Every asserted
device fact in these docs traces to one of:

- **[V]** — the vendor documents (SDK Description, User Manual, quick guides in
  `~/Downloads/slc_series_led_controller_software/`).
- **[HW]** — empirically verified against the real SLC-SA04-U/S by the old test
  project (`~/Developer/Projects/mightex-slc-test`).
- **[C]** — a library convention or decision of ours, not a device fact.

Anything without a tag in `device_and_protocol.md` should be treated as
unverified. When adding new device claims, tag them or label them conventions.

## Deprecated artifacts (reference only — do not build on these)

| Artifact | Location | Status |
|---|---|---|
| Contract branch | `~/Developer/Projects/mightex-slc` (branch `contract`) | Abandoned. Porting source for contract models; see `lineage.md`. |
| First test project | `~/Developer/Projects/mightex-slc-test` | Deprecated. Only code ever run against real hardware; its learnings are folded into `device_and_protocol.md` and `architecture.md`. |
| Original plan draft | `~/Downloads/slice_build_plan_normal_mode_timed_on.md` | Superseded by `build_plan_normal_mode_timed_on.md` here. |
| Vendor PDFs | `~/Downloads/slc_series_led_controller_software/` | The two authoritative documents are converted to markdown in `docs/vendor/`; the remaining two quick guides contain nothing protocol-relevant. |
