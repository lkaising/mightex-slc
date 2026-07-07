# mightex-slc docs

Reorganized 2026-07-06 by trust tier, so it's clear at a glance which documents
to believe. **When sources disagree: real hardware > `vendor/` > the live code
under `src/mightex_slc/` > `reference/` > `stale/`.**

| Folder | Trust | What's in it |
|---|---|---|
| **[`handoff/`](handoff/)** | start here | [`rs232_backend_handoff.md`](handoff/rs232_backend_handoff.md) — the map for building the real RS232 backend and bringing the `normal_mode_timed_on` slice to a hardware-real state. A pointer doc; it routes you to everything below. |
| **[`vendor/`](vendor/)** | authoritative | The two 2018 vendor documents — SDK Description v1.1.4 (the command set) and User Manual v1.3.6 (modes, module matrix, limits, safety). The ultimate authority on the wire protocol. |
| **[`reference/`](reference/)** | mostly current — **verify** | [`architecture.md`](reference/architecture.md) (the layered design + the RS232 recipe) and [`device_and_protocol.md`](reference/device_and_protocol.md) (the consolidated hardware/protocol reference, including §9's hardware-proven "goldmine"). Valuable, but carry stale threads (macOS/path assumptions, "RS232 is future" framing) — see the handoff doc §10. |
| **[`stale/`](stale/)** | history + ideas — **do not trust literally** | `build_plan_normal_mode_timed_on.md`, `phase_status.md`, `lineage.md`, and the old `README.md`. Good design thinking and project history, but out of pace with the code (e.g. the phase ledger says the public API is unbuilt — it is fully built). Verify every concrete claim against the vendor docs, the live code, and real hardware. See the handoff doc §11. |

New to this project? Read [`handoff/rs232_backend_handoff.md`](handoff/rs232_backend_handoff.md) first — it explains the current state, the mission, and where each fact lives.
