# Phase Status — `normal_mode_timed_on` slice

Progress ledger for [`build_plan_normal_mode_timed_on.md`](build_plan_normal_mode_timed_on.md).
One row per phase; the plan holds the detail, this file holds only where we
are. Update the row when a phase's gate passes.

Statuses: `not started` / `in progress` / `complete`.

| Phase | Scope | Gate / completion condition | Status | Completion note |
|---|---|---|---|---|
| 0 | Prep: `pyproject.toml`, root `__init__.py` stub, this ledger | `python -m pip install -e ".[dev]"` succeeds; `import mightex_slc` works | complete | 2026-07-04. Hatchling + src/ layout authored (Python >=3.11); root stub created; build plan clarified (Phase 0/1 split; `NormalParameters` question recorded as Phase 1 investigation). Gate passed: editable install from the sibling `examples/` environment succeeded; `import mightex_slc` resolved to `src/mightex_slc/__init__.py`; metadata reported version 0.0.0. |
| 1 | Contract foundation: port six operations, six components, two bases; write schema generator; generate schemas; staleness test | `import mightex_slc.contract` works; each operation's valid request round-trips, invalid rejected; schemas generated and staleness test green | not started | Open investigation: `NormalParameters` read-path-only vs. reuse in `configure_normal` (plan §6, Phase 1). |
| 2 | Transport seam and fake: `transport/base` interface, in-memory fake device | Fake implements the interface with per-channel state and real configure-then-activate semantics | not started | |
| 3 | Tracer bullet: `enumerate_devices` end to end | Integration test returns a non-empty descriptor list from the fake through the full seam | not started | |
| 4 | Fan out the remaining five operations | Each of the six operations round-trips against the fake in isolation | not started | |
| 5 | Public surface: errors, types, discovery, proxies, root `__init__.py` exports | The example's imports resolve from `mightex_slc` | not started | |
| 6 | Tests and acceptance: contract tests, integration test, run the example | `examples/normal_mode_timed_on.py` completes cleanly against the fake | not started | |
