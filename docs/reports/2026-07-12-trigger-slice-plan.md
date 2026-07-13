# Trigger Slice — Loose Plan

**Status: a working sketch, not a spec.** This records the current thinking
for bringing TRIGGER-mode configuration into the library, informed by the
2026-07-12 bench session ([probe report](2026-07-12-trigger-bench-probes.md),
now folded into [`protocol.md`](../developing/protocol.md)). Direction and
shape here are considered settled *enough to start*; anything marked **open**
is genuinely undecided, and even the settled parts should bend if
implementation or the bench pushes back. Nothing below has been built.

## Where this starts from

The library configures NORMAL mode end to end and the pattern is proven:
a frozen contract model per device storage area (`NormalParameters`), one
request/reply operation pair per verb, codec functions as the only place wire
strings are spelled, capability policy in the server's channel model, and a
fake transport that keeps the whole stack testable without hardware.

The bench session removed the blockers that made trigger mode harder than
NORMAL:

- `?TRIGGER` reads back fresh immediately — no settle.
- `?TRIGP` framing is characterized and stable — a structured profile getter
  is implementable, not deferred.
- The device validates nothing (clamps or stores garbage, always `##`), so
  contract-level validation and read-back verification carry real weight.
- The device does not enforce disable-before-reprogram; the library owns
  that rule.
- Factory trigger defaults are now known (Imax 10 mA, polarity 0, one
  (10 mA, 20 µs) step) — the fake can be honest.

## Direction

Two independent set/get pairs, mirroring the device's two storage areas —
not one combined object:

```python
channel.set_trigger_parameters(TriggerParameters(current_max_ma=1000,
                                                 polarity=TriggerPolarity.RISING))
channel.get_trigger_parameters()          # -> TriggerParameters

channel.set_trigger_profile(StepProfile(steps=(ProfileStep(current_ma=500,
                                                           duration_us=2000), ...)))
channel.set_trigger_profile(FollowerProfile(current_ma=100))
channel.get_trigger_profile()             # -> the same union, reconstructed

channel.set_active_mode(OperatingMode.TRIGGER)   # arming stays where it is
```

Reasoning, briefly: the pairs map 1:1 to `TRIGGER`/`?TRIGGER` and
`TRIGP`/`?TRIGP`, each pair is independently verifiable (which matters now
that an ack provably doesn't mean stored-as-written), and the profile types
are reusable when STROBE arrives (`STRP` has the same step semantics;
`FollowerProfile` stays trigger-only). The follower special case is an
explicit type so the wire sentinel `9999` never appears in a public field —
it lives in the codec only.

Likely model sketch (shapes provisional, constraints not):

- `TriggerPolarity` — IntEnum, wire codes 0/1. The device stores polarity 2
  verbatim, so this enum is the only thing standing between a typo and
  garbage on the device.
- `ProfileStep(current_ma, duration_us)` — current ≥ 0; duration 1..99,999,999.
- `StepProfile(steps=…)` — 1..127 steps; **must reject a first step of
  9999 µs** (the device would silently reinterpret it as follower mode —
  refuse rather than reinterpret).
- `FollowerProfile(current_ma)` — expands to `TRIGP ch 0 I 9999` + terminator.
- Discriminated union over a `kind` field, like the existing reply unions.

## Rough shape by layer

Same lifecycle order as previous slices; none of this is exotic:

1. **Contract** — components above + three or four operations
   (`set/get_trigger_parameters`, `set_trigger_profile`,
   `get_trigger_profile`) as standard Request/Ok/Reply triples.
2. **Codec** — `encode_trigger`, `encode_query_trigger`, `parse_trigger`
   (last-two-tokens style), `encode_trigger_profile` returning the full
   command list terminator-included, and a `parse_trigger_profile` built on
   the bench-derived grammar (strip `#`, split lines, pairs until `0 0`;
   first-step 9999 maps back to `FollowerProfile`).
3. **Transport** — new interface methods; the rs232 profile getter needs the
   **extended quiet-drain read** (the standard 20 ms drain truncates the
   multi-line response — this is the one genuinely new mechanism in the
   slice, and probably wants its own function in `serial_link`).
4. **Fake** — trigger state per channel with the *measured* factory defaults;
   clamp behavior mimicking the bench (or rejecting instead — **open**,
   see below). The fake is an MA04 (no trigger), so seam-level happy-path
   tests need a trigger-capable preset — likely an SA04 variant reachable
   via `open_device(transport=FakeTransport(...))` without changing
   `open_fake_device()`.
5. **Server** — `supports_trigger_mode` guard on all four operations,
   profile length vs `capabilities.max_profile_steps`.
6. **Client, schemas, docs, tests** — mechanical mirroring of the NORMAL
   slice; api.md gets the disable-first sequence and the ack-is-not-verify
   caveat prominently.

## Open questions (deliberately unlocked)

- **Should the fake clamp like the real device, or reject?** Clamping is
  bench-faithful and lets tests exercise the verify-by-read-back story;
  rejecting is safer-feeling but fictional. Leaning bench-faithful.
- **Does `set_trigger_profile` verify by read-back?** The device clamps
  silently, so a set-then-get compare inside the operation would catch
  clamps — but it doubles wire traffic and no other setter does this.
  Current lean: keep setters pure, document the verify workflow, let the
  caller (or a future convenience helper) do program → verify.
- **Profile-length guard strictness** — the SA04 acks step index 127 happily,
  and whether "2 Steps" families lose a step to the terminator is still
  §9.6-open. Guarding at `max_profile_steps` is the conservative default;
  it may turn out to be stricter than the hardware.
- **Naming** — `StepProfile`/`FollowerProfile` vs `TriggerProfile`/
  `TriggerFollower` or similar; decide when STROBE reuse is closer.
- **Whether the armed-reprogram rule ever becomes a guard** — for now it's
  documentation only; revisit if execution-level testing shows armed
  reprogramming corrupts playback.

## Bench follow-ups (not blocking, fold in when hardware time is cheap)

From protocol.md §9 items 9–12: execution-level behavior (needs a trigger
source wired), the acked-but-unread limit cases (Tset overflow, step 128,
non-first 9999 — one short read-back probe would close these), re-clamping
on later Imax changes, and whether `#?` can occur at all for trigger config.
None of these block the slice; the first one is the only prerequisite for
ever trusting playback semantics.

## Not in this slice

STROBE configuration (reuses the profile types later), load voltage, FanPWM,
any convenience orchestration (e.g. a one-call "configure and arm"), and any
attempt to model execution/playback behavior — the bench hasn't seen a
profile play yet, and the library shouldn't pretend otherwise.
