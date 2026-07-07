# Lineage — where this project came from, and what stays behind

Status: written 2026-07-04. This document exists so the deprecated artifacts
can be closed out with a clear conscience: what each one was, what was taken
from it, and what is deliberately left behind. After reading this, nothing in
the old folders should need to be consulted except as a porting reference.

---

## The three predecessors

| # | Artifact | Where | Verdict |
|---|---|---|---|
| 1 | **Test project** (`mightex-slc-test`) | `~/Developer/Projects/mightex-slc-test` | Deprecated. The only code ever run against real hardware. Its empirical knowledge is fully extracted into `device_and_protocol.md`. |
| 2 | **Contract branch** (`mightex-slc`, branch `contract`) | `~/Developer/Projects/mightex-slc` | Abandoned. Its device-fact corpus, API naming, error model, and contract models are salvaged; its process and structure are not. Porting source for Phase 1. |
| 3 | **Plan draft** | `~/Downloads/slice_build_plan_normal_mode_timed_on.md` | Superseded by `build_plan_normal_mode_timed_on.md` in this folder, which fixes its stale references. |

The current project — `~/Developer/Projects/mightex/mightex-slc`, branch
`slice/normal-mode-timed-on` — is attempt three, and structurally it is the
contract branch's architecture with the contract branch's *process* inverted:
one thin vertical slice through all layers instead of one layer built to
completion.

---

## 1. The test project (first attempt, ~May 2026)

A flat, pragmatic driver: `transport.py` (serial I/O) → `protocol.py`
(commands, validation, parsing) → `controller.py` (user API), plus CLI scripts
that ran real experiments — LED ramp tests, strobe profiles, and a
YAML-config-driven trigger-follower programmer used for NIR imaging with an
Arduino frame-sync.

**What it proved** (now folded into the new docs):

- The entire RS232 recipe in `device_and_protocol.md` §9 — terminators, the
  20 ms drain, per-command buffer resets, substring acks, the `?CURRENT`
  calibration-field trap, the 0.3 s parameter-settle, the unacked `ECHOOFF`,
  the disable-in-`finally` safety habit. All of it verified on a real
  SLC-SA04-U/S.
- The **three-layer transport split** (bytes / meaning / API) with a pure
  command codec — it made the whole stack testable against a ~70-line fake
  serial object. The new `transport/rs232` design (`architecture.md` §6)
  inherits this shape directly.
- Validate-before-send, named-constant limits, a custom exception hierarchy,
  hardware tests behind an opt-in pytest marker, and program → verify →
  only-then-`STORE` gating.

**Its weak spots** (do better this time): query-response parsing was never
made robust (`?TRIGP`'s parser was deleted in favor of substring matching);
the empirically-required delays lived in tests and heuristics rather than the
driver; no thread safety, retries, or port discovery; a monolithic package
with no seam for a fake *device* (only a fake serial port).

**Closure:** nothing left to extract. The repo can sit untouched as an
archive; its `docs/command_reference.md` and `config/trigger_config.yaml`
(the real deployed LED currents) are the only files worth revisiting, and
their contents are reflected in `device_and_protocol.md` §1 and §6.

## 2. The contract branch (second attempt, ~Jun 30 – Jul 3, 2026)

The plan was to build the entire contract layer first — every operation the
device supports, modeled, validated, schema-generated, and "locked" — then
build client, server, and transport beneath it. It lasted four days.

**What it produced that we keep:**

- **The device-fact corpus.** `docs/temp_mightex_slc.py` (an 830-line
  docstring-only API skeleton) and `docs/temp_mightex_knowledge_transfer.md`
  (the decision log) contain carefully reviewed device behavior — the
  configure-then-activate model, one-based channels, per-family current
  resolution, volatile-until-STORE persistence, capability variance across
  module families, the single-condition device error model. All merged into
  `device_and_protocol.md`.
- **The traceability rule** — every device fact traces to a document or is
  labeled a convention. Born when a skeleton draft was caught *fabricating*
  device facts (an invented current resolution, a nonexistent trigger
  sub-mode). Adopted permanently; it is the provenance-tag system in these
  docs.
- **The public API naming**, reused verbatim: `open_device`, `Controller`,
  `Channel`, `configure_normal(current_max_ma, current_set_ma)`,
  `set_active_mode`, `OperatingMode`. (`enumerate_devices` was also carried
  over initially, then removed 2026-07-06 when the API went
  serial-target-first — the vendor's enumerate/open-by-index flow is
  USB/HID-only, and this library is RS232-only.)
- **The error model**: the `MightexLEDError` hierarchy and the `ErrorType`
  reply-to-exception mapping (`architecture.md` §4).
- **The contract models themselves** — complete and well-made. The slice's
  operations, components, and two bases are ported from
  `contract/mightex_contract/`, not rewritten (the ported `enumerate_devices`
  operation and `DeviceDescriptor` component were later removed, and
  `open_device` reshaped, in the 2026-07-06 serial-target refactor).
- **The cut list**: no message broker, no C++/DLL binding, no second
  validation layer. Settled; do not reopen those debates.
- The working schema generator, as a reference implementation only.

**Why it was abandoned** — named concretely so it isn't repeated:

1. **Breadth before contact with reality.** 54 model classes across 18
   operations were authored and "locked" before a single byte had ever been
   exchanged with the device. The real risk — the RS232 protocol — was
   sequenced dead last and never reached. The branch died with zero I/O, zero
   tests, and four empty top-level packages (`client/`, `server/`,
   `transport/`, `tests/` — all `.gitkeep`; the transport directory was even
   misspelled `rs323` and nobody noticed, because nothing was ever put in it).
2. **An artifact pipeline with no customers.** 32 committed YAML schema files
   (~2,800 lines), a determinism regime, and exact version pins — for output
   nothing consumed.
3. **A meta-work spiral.** Two of the branch's four documents are a 447-line
   audit *of the generated schemas* and a 285-line refactoring plan *for the
   generator*. The final days went to the project studying its own exhaust.
4. **Structure ahead of need.** Four top-level packages for an in-process,
   single-consumer library (the unresolved layout even blocked writing a
   `pyproject.toml`); one-concept-per-file granularity that was itself
   re-shuffled repeatedly (the `__pycache__` fossils record at least two
   layout refactors of the same package).
5. **Governance ceremony for a solo pre-v0 project** — "locked decisions,"
   "definition of locked," contract-change-as-deliberate-act — process weight
   with no working code under it.

The architecture itself was *not* the problem — the current branch keeps it.
The failure was building it breadth-first and polishing upstream layers
against no downstream consumer. The slice method is the corrective.

**Closure:** consult it exactly twice more — Phase 1 ports the slice's
contract models from `contract/mightex_contract/`, and the schema generator
is written against `contract/generate_schemas.py` as reference. Its two
`temp_*` docs are superseded by this folder (their device facts are merged;
their device-facing open questions are carried in `device_and_protocol.md`
§10; their design-facing ones are settled in the build plan's decision record,
§11). Nothing else in the branch should be opened again.

## 3. The plan draft in Downloads

Written for this branch, and substantially correct — its phases, scope, and
seam design are kept intact. It was drafted with the contract branch's state
in mind, though, so it described several things as "already ported, needs
fixing" that in fact never left the old branch. The corrected edition in this
folder (`build_plan_normal_mode_timed_on.md`) fixes, specifically: the
porting-vs-fixing framing, the empty `pyproject.toml`, the generator that must
be written rather than updated, the staleness check that never existed, and
the now-resolved `close_device` question. The Downloads copy can be deleted.

---

## Rules going forward

1. **This `docs/` folder is the source of truth.** Old folders are read-only
   archives.
2. **Old ideas do not migrate implicitly.** Anything carried forward from a
   predecessor must appear in these docs first (with provenance, if it is a
   device fact).
3. **The vendor documents are the ultimate authority on the wire protocol.**
   Resolved 2026-07-04: the two authoritative ones (*SDK Description* v1.1.4
   and *User Manual* v1.3.6) are converted to markdown and live in-repo at
   `docs/vendor/`. The original PDFs — plus the two quick guides, which
   contain nothing protocol-relevant — remain in
   `~/Downloads/slc_series_led_controller_software/`.
