# Trigger Bench Probe Report — 2026-07-12

Five hardware probes were run against the bench controller to resolve every
open unknown blocking the TRIGGER-mode slice (`set_trigger_parameters`,
`get_trigger_parameters`, and the trigger-profile operations). All five
completed successfully, the device was restored to its pre-session state, and
`STORE` was never sent — nothing was persisted.

This report is self-contained: it records what was unknown and why, how each
probe worked, the raw wire evidence, what the findings mean for the library,
and what remains unverified. Claims follow the provenance convention of
[`../developing/protocol.md`](../developing/protocol.md): **[V]** vendor-documented,
**[HW]** verified on real hardware, **[C]** a library convention.

## Headline findings

1. **`?TRIGGER` read-back needs no settle.** 50/50 immediate reads after a
   `TRIGGER` write came back fresh. **[HW]**
2. **Protocol quirk #9 is resolved.** The `?TRIGP` response format is stable
   and parseable under per-command buffer hygiene: one `Iset Tset` line per
   step, terminator line included, byte-identical across repeated reads. The
   historical "unstable/undocumented" verdict is attributed to the
   predecessor driver's weaker read strategy, not the firmware. A structured
   `get_trigger_profile` is now unblocked. **[HW]**
3. **The device validates almost nothing — it clamps or stores garbage,
   always answering `##`.** Out-of-range Imax silently clamps to the pulsed
   ceiling; a profile step current above the stored trigger Imax silently
   clamps to that Imax at write time; an invalid polarity (`2`) is stored
   verbatim; out-of-range step indexes and durations are acknowledged.
   Client-side validation is therefore load-bearing, not defensive. **[HW]**
4. **Reprogramming while armed is silently accepted.** `TRIGGER` and `TRIGP`
   sent during active TRIGGER mode ack, take effect, and leave the channel
   armed. The disable-before-reprogram rule is entirely the library's to
   enforce. **[HW]**
5. **Factory trigger defaults contradict the vendor docs.** After
   `RESTOREDEF`, every channel reads TRIGGER **Imax = 10 mA** (documented:
   20 mA) with polarity 0, and the factory trigger profile is **not empty**
   — it is one step of (10 mA, 20 µs) plus the terminator. **[HW]**

## Bench setup

| | |
|---|---|
| Device | Mightex SLC-SA04-U/S (4-channel SA family) |
| Firmware | 3.1.8 (`Mightex LED Driver:3.1.8`) |
| Serial number | 04-251013-011 |
| Connection | `/dev/ttyUSB0`, 9600 N-8-1, 1.0 s read timeout, Linux |
| Date | 2026-07-12 |
| Trigger input | **Not connected** — no external trigger source was wired |
| LED load | None relevant; no channel ever left DISABLE outside probe 4's brief arm |

This is the same bench unit and path as every prior **[HW]** claim in
`protocol.md`. Because the trigger input was never wired, **no profile was
ever executed**: every finding below is at the command/storage layer
(acknowledgement and read-back), not the playback layer. Execution-level
behavior remains untested (see [Remaining unknowns](#remaining-unknowns)).

The probe scripts live outside the library in the sibling `examples/`
directory and spell the trigger wire strings locally — the library codec had
no trigger encoders at probe time, and the library itself was not modified:

| Script | Question it answers |
|---|---|
| `examples/probe_trigger_settle.py` | Is an immediate `?TRIGGER` read after a `TRIGGER` write fresh? |
| `examples/probe_trigp_readback.py` | What is the raw `?TRIGP` response framing for known profiles? |
| `examples/probe_trigger_limits.py` | How does the device answer boundary/out-of-range trigger arguments? |
| `examples/probe_trigger_armed_reprogram.py` | Does the device refuse `TRIGGER`/`TRIGP` while the channel is armed? |
| `examples/probe_trigger_factory_defaults.py` | What are the factory-default trigger parameters and empty-profile framing? |

## Method and safety conventions

Every probe follows the project's established bench discipline:

- **Human gate**: without `--yes`, a probe prints its exact write plan and
  exits before opening the serial port.
- **Precondition**: every channel must read `?MODE` = 0 (DISABLE) before any
  write; otherwise the probe aborts.
- **Volatile only**: `STORE` is never sent. A power cycle reloads the last
  STOREd state regardless of anything a probe did.
- **Record and restore**: original values are read first and rewritten in a
  `finally` block, with read-back verification and a final mode check.
- Parameter writes on a disabled channel store state without driving output;
  only probe 4 ever sent `MODE`, and only on channel 1, briefly.

Two read recipes were used:

- The proven standard exchange: `reset_input_buffer()` → write command +
  `\n\r` → `read_until(b"\r")` → 20 ms drain of `in_waiting`.
- An **extended quiet-drain** capture for `?TRIGP`: after `read_until(b"\r")`,
  keep reading until the line has been quiet for 0.3 s (capped at 3 s). The
  `?TRIGP` response is multi-line, so the first CR is *not* the end of the
  response, and at 9600 baud the remainder trickles in slower than a single
  20 ms drain can catch. This distinction matters for implementation — see
  [Implications](#implications-for-the-library).

## Probe 1 — `?TRIGGER` settle (`probe_trigger_settle.py`)

**Question.** The NORMAL-mode twin of this probe cleared the historical 0.3 s
post-write settle on 2026-07-11. Does the TRIGGER parameter pair behave the
same, or does `get_trigger_parameters` need a delay?

**Procedure.** 50 trials alternating `TRIGGER 1 40 0` and `TRIGGER 1 60 1`
(both fields alternate so a stale read of either is caught), each followed by
an immediate `?TRIGGER 1` under the standard exchange recipe. On mismatch the
probe would wait 0.3 s and re-read.

**Result.** 50/50 immediate reads fresh; the mismatch path never ran.

```text
TX 'TRIGGER 1 40 0'   RX '##'
TX '?TRIGGER 1'       RX '#40 0'     <- immediate, fresh (representative trial)
```

**Conclusion.** `?TRIGGER` after `TRIGGER` needs no settle under per-command
reset + drain hygiene, matching the NORMAL-mode result. **[HW]**

Incidentally re-confirmed: the `?TRIGGER` response shape is `#Imax Polarity`
exactly as documented, with no leading calibration fields (unlike
`?CURRENT`). **[V][HW]**

## Probe 2 — `?TRIGP` framing (`probe_trigp_readback.py`)

**Question.** Protocol quirk #9: the `?TRIGP` response format was recorded as
"unstable/undocumented"; a structured parser was written, tested, and
abandoned by the predecessor project. That verdict predates the buffer
hygiene that cleared the NORMAL settle myth. What does the response actually
look like, and is it stable?

**Procedure.** With `TRIGGER 1 100 0` stored (so every step current used is
legal), write four known profiles to channel 1 and capture the raw `?TRIGP 1`
bytes after each with the extended quiet-drain recipe. Every capture was
taken twice to test read-to-read stability. A baseline capture of the
pre-session profile was taken first.

**Result.** Every capture was byte-identical across its two reads:

| Profile written | Raw `?TRIGP 1` capture |
|---|---|
| baseline (pre-session state) | `b'#10 20 \r\n 0 0 \r\n'` |
| single-step: (50, 2000), (0, 0) | `b'#50 2000 \r\n 0 0 \r\n'` |
| two-step: (50, 2000), (10, 100000), (0, 0) | `b'#50 2000 \r\n 10 100000 \r\n 0 0 \r\n'` |
| follower: (20, 9999), (0, 0) | `b'#20 9999 \r\n 0 0 \r\n'` |
| all-off: (0, 0) at step 0 | `b'#0 0 \r\n'` |

**Derived response grammar** (fw 3.1.8): **[HW]**

```text
#Iset0 Tset0 <SP><CR><LF>
<SP>Iset1 Tset1 <SP><CR><LF>
...
<SP>0 0 <SP><CR><LF>
```

- One line per profile step, **including the (0, 0) terminator line**.
- `#` prefixes the first line only; continuation lines begin with a space.
- Every line carries a trailing space before `\r\n` (the same trailing-space
  habit `DEVICEINFO` shows).
- The dump **stops at the first (0, 0)**: steps stored beyond the terminator
  are not reported (the two-step profile's stale step 2 never appeared in the
  follower capture that followed it).
- The follower sentinel `Tset = 9999` reads back verbatim.
- A profile whose step 0 is the terminator reads back as the single line
  `#0 0`.

**Conclusion.** The format is regular and directly parseable with the
project's proven tolerant style (strip `#`, split lines, take token pairs,
stop at `0 0`). The historical instability is attributed to the predecessor
reading only to the first CR — which truncates this response by design —
plus weaker buffer hygiene, not to firmware nondeterminism. Quirk #9 should
be considered resolved for fw 3.1.8, and a structured `get_trigger_profile`
is implementable. **[HW]**

## Probe 3 — accept/reject boundaries (`probe_trigger_limits.py`)

**Question.** Where does the device draw its `#?` rejection lines for
`TRIGGER` and `TRIGP` arguments — Imax ceilings, polarity, step index range,
duration range, and step currents above the stored trigger Imax?

**Procedure.** Twelve boundary commands on channel 1, all while DISABLE, each
classified by response type. `?TRIGGER` was read back after every `TRIGGER`
case to observe stored state; a raw `?TRIGP` capture followed the
step-current-above-Imax case. The TRIGP cases ran with `TRIGGER 1 100 0`
stored first.

**Result.** *Every one of the twelve commands answered `##`.* No `#?` was
ever observed. Stored state told the real story:

| Case | Response | Stored state after |
|---|---|---|
| `TRIGGER 1 1000 0` (NORMAL ceiling) | `##` | Imax 1000 — stored verbatim |
| `TRIGGER 1 1500 0` (between ceilings) | `##` | Imax 1500 — stored verbatim |
| `TRIGGER 1 3500 0` (pulsed ceiling) | `##` | Imax 3500 — stored verbatim |
| `TRIGGER 1 3501 0` (above pulsed ceiling) | `##` | **Imax 3500 — silently clamped** |
| `TRIGGER 1 20 2` (invalid polarity) | `##` | **polarity 2 — stored verbatim** |
| `TRIGP 1 0 500 2000` (step current 500 > Imax 100) | `##` | **step stored as (100, 2000) — current silently clamped to the stored trigger Imax at write time** |
| `TRIGP 1 2 10 1000` (index 2 on a vendor-"2 Steps" family) | `##` | not read back |
| `TRIGP 1 127 0 0` (max documented index) | `##` | not read back |
| `TRIGP 1 128 0 0` (index out of documented range) | `##` | not read back |
| `TRIGP 1 0 50 99999999` (Tset at documented max) | `##` | not read back |
| `TRIGP 1 0 50 100000000` (Tset above documented max) | `##` | not read back |
| `TRIGP 1 1 50 9999` (9999 on a non-first step) | `##` | not read back |

**Conclusions.** **[HW]**

- The SA04 pulsed-mode ceiling of 3500 mA is real but enforced by **silent
  clamping**, not rejection. An ack does not mean the device stored what was
  written.
- Step currents are clamped against the trigger Imax **at TRIGP write time**.
  Consequence: `TRIGGER` must be written before `TRIGP` (the proven safe
  sequence already does this), and whether a later Imax change re-scales
  already-stored steps is unknown.
- The device will store a **meaningless polarity**. Nothing device-side
  prevents `polarity 2`; what an armed channel does with it is untested.
- No argument tested here produces `#?`. For trigger configuration on this
  firmware, the response-code table's `#?` row is effectively theoretical:
  **client-side validation is the only validation that exists.**

## Probe 4 — reprogramming while armed (`probe_trigger_armed_reprogram.py`)

**Question.** The hardware-proven rule is disable-before-reprogram (protocol
quirk #10), but does the device *enforce* it — rejecting `TRIGGER`/`TRIGP`
under an active TRIGGER mode — or must the library own the rule?

**Procedure.** With the trigger input physically disconnected (an armed
channel stays dark with no edge source): program a safe configuration while
disabled (`TRIGGER 1 20 0`; profile (10 mA, 1000 µs) + terminator), arm with
`MODE 1 3`, then while armed send `TRIGGER 1 30 0` and `TRIGP 1 0 10 2000`,
reading `?TRIGGER` and `?MODE` after each. Disarm, restore.

**Result.**

```text
TX 'MODE 1 3'          RX '##'    ?MODE -> #3   (armed)
TX 'TRIGGER 1 30 0'    RX '##'    ?TRIGGER -> #30 0   (write TOOK)   ?MODE -> #3
TX 'TRIGP 1 0 10 2000' RX '##'                                       ?MODE -> #3
TX 'MODE 1 0'          RX '##'    ?MODE -> #0   (disarmed)
```

**Conclusion.** Both writes were acknowledged and took effect while armed,
and the channel stayed in TRIGGER mode throughout. The device enforces
nothing: disable-before-reprogram is entirely a host-side rule. What a
mid-playback reprogram does to an *executing* profile remains untested (no
trigger source was connected, so playback never ran). **[HW]**

## Probe 5 — factory defaults (`probe_trigger_factory_defaults.py`)

**Question.** The vendor documents factory defaults as "STROBE and TRIGGER
Imax 20 mA with empty profiles" but never states the default trigger
polarity, and the `?TRIGP` shape of a factory-fresh profile had never been
captured.

**Procedure.** Record every channel's NORMAL and TRIGGER values, send
`RESTOREDEF` (volatile-only factory reset; all channels were already
DISABLE, so no output could change), read the factory trigger state, then
rewrite the recorded values. Trigger/strobe profiles cannot be rewritten from
records (their pre-state predates this session), so they remain at factory
values — which on this unit matched the pre-session state anyway.

**Result.** After `RESTOREDEF`, on all four channels:

| Setting | Vendor claim | Observed (fw 3.1.8) |
|---|---|---|
| TRIGGER Imax | 20 mA | **10 mA** |
| TRIGGER polarity | *undocumented* | **0 (rising)** |
| Trigger profile | "empty" | **one step (10 mA, 20 µs) + terminator** — raw: `b'#10 20 \r\n 0 0 \r\n'` |
| NORMAL Imax/Iset (control) | 20 / 10 mA | 20 / 10 mA — matches docs |

The NORMAL control matching its documented value shows the discrepancies are
real, not a parsing artifact. The pre-session baseline capture in probe 2 was
byte-identical to the post-`RESTOREDEF` capture, i.e. this unit's trigger
configuration had never been customized — which corroborates the reading but
also means the two observations are not fully independent.

**Conclusion.** The vendor's factory-default claims are wrong for the
trigger area on this firmware: Imax defaults to 10 mA, not 20, and the
default profile is a single (10 mA, 20 µs) step, not empty. (20 µs is the
SA-family timing resolution — plausibly the firmware's minimal placeholder
step.) The default polarity, previously undocumented, is 0/rising. **[HW]**

## Implications for the library

For the planned trigger slice (two set/get pairs: `TriggerParameters` =
Imax + polarity over `TRIGGER`/`?TRIGGER`; a profile object over
`TRIGP`/`?TRIGP`):

1. **`get_trigger_parameters` can be wired with no settle**, exactly like
   `get_normal_parameters`.
2. **`get_trigger_profile` is unblocked.** The response grammar above is
   stable and parseable. The transport read for it must use an extended
   quiet-drain (read to first CR, then keep draining until the line is
   quiet), because the response is multi-line — the standard single-drain
   exchange would truncate it.
3. **Contract-level validation is load-bearing.** The device stores polarity
   2 and clamps out-of-range currents while answering `##`. Model-level
   constraints (polarity as a two-value enum, current/duration bounds, the
   reserved first-step-9999 rule) are the only rejection path a user gets.
4. **An ack is not a verify.** Because the device clamps silently, the
   program → verify → persist workflow should compare read-back against
   intent for trigger settings; with `?TRIGP` now parseable, that check is
   possible for profiles too.
5. **Write `TRIGGER` before `TRIGP`** — step currents are clamped against
   the Imax stored at write time. The documented safe sequence already has
   this order; it is now known to be load-bearing.
6. **The library owns disable-before-reprogram.** The device accepts armed
   reprogramming silently, so the rule survives only as documentation (or an
   explicit guard, if ever justified by an execution-level failure).
7. **The fake device's trigger factory defaults** should model the bench
   observation — Imax 10 mA, polarity 0/rising, profile = (10 mA, 20 µs) +
   terminator — tagged **[HW]**, with the vendor's contradicted "20 mA /
   empty" claim noted.

## Remaining unknowns

Resolved by this session: `?TRIGP` framing (quirk #9), `?TRIGGER` settle,
armed-reprogram acceptance, factory trigger defaults, clamp-vs-reject
behavior for Imax and step currents.

Still open — do not resolve from memory:

1. **Execution-level behavior is entirely untested.** No trigger source was
   connected, so no profile ever played. Unknown: actual pulse playback,
   trigger latency, follower-mode output, restart-on-retrigger, and what an
   armed channel does with a stored garbage polarity (2) or a mid-playback
   reprogram.
2. **The vendor-"2 Steps" family question (protocol.md §9.6) is still open.**
   Step indexes 2, 127, and even 128 all *ack* on this SA04, so the write
   layer draws no line; whether steps beyond the family limit *execute* is
   an execution-level question. (A follow-up `?TRIGP` read-back after
   writing a >2-step profile would at least show whether they are stored;
   this session's captures never exceeded two active steps.)
3. **Stored values for the unread limit cases**: Tset 100,000,000 (clamped to
   99,999,999? stored verbatim?), the step-128 write (ignored? wrapped?),
   and 9999 on a non-first step (stored as a plain duration?) were acked but
   not read back.
4. **Re-clamping**: whether changing TRIGGER Imax after a profile is stored
   re-scales, re-clamps, or leaves already-clamped step currents.
5. **Whether any trigger-config argument can produce `#?` at all** on this
   firmware, or whether the response-code table's `#?` row simply does not
   apply to `TRIGGER`/`TRIGP`.
6. Everything in protocol.md §9 not touched here (the `Error` command, QA
   resolution, non-Linux serial behavior, ...).

## End-state accounting and reproduction

Every probe verified at exit: all channels DISABLE, channel values restored
to their recorded pre-session state (`TRIGGER 10 0` on all channels, NORMAL
20/10), trigger profile at the factory (10 mA, 20 µs) step — identical to the
pre-session baseline. `STORE` was never sent, so the device's non-volatile
state was never written and a power cycle reloads the last STOREd state
regardless.

To reproduce (each script prints its full write plan and exits without
`--yes`; run order is least- to most-invasive):

```bash
cd examples
.venv/bin/python probe_trigger_settle.py --yes /dev/ttyUSB0
.venv/bin/python probe_trigp_readback.py --yes /dev/ttyUSB0
.venv/bin/python probe_trigger_limits.py --yes /dev/ttyUSB0
.venv/bin/python probe_trigger_armed_reprogram.py --yes /dev/ttyUSB0   # arms ch 1; disconnect the trigger input first
.venv/bin/python probe_trigger_factory_defaults.py --yes /dev/ttyUSB0  # sends RESTOREDEF (volatile)
```
