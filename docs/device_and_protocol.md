# Mightex SLC — Device & Protocol Reference

Status: source of truth as of 2026-07-04. Consolidates the vendor documentation
with everything empirically learned from real hardware by the deprecated test
project. Provenance tags: **[V]** vendor docs, **[HW]** verified on the real
device, **[C]** library convention. See `README.md` for the full legend.

Vendor sources — converted to markdown in-repo at [`vendor/`](vendor/):
- *SDK Description* v1.1.4 (2018) — the authoritative command set.
- *User Manual* v1.3.6 (2018) — modes, module matrix, safety, MA04-MU §3.0.

(The original PDFs, plus two quick guides with nothing protocol-relevant in
them, remain in `~/Downloads/slc_series_led_controller_software/`.)

---

## 1. Our hardware

The unit everything was actually tested on **[HW]**:

- **Mightex SLC-SA04-U/S**, firmware **3.1.8**, serial **04-251013-011**.
  4-channel, SA family: 2-step profiles, no voltage monitoring, trigger mode
  present, 1 mA current resolution, 1 A NORMAL / 3.5 A pulsed ceilings.
- Connected over serial at `/dev/ttyUSB0` on Linux (USB-serial path). The new
  environment is macOS, where the device path is `/dev/cu.usbserial-*` instead
  — the user identifies and names it (the library never scans for ports), and
  nothing in any prior project covers macOS yet. **[C]**
- Bench LEDs (Thorlabs): CH1 **M850L3** (850 nm, capped 1000 mA by NORMAL
  mode; datasheet 1200 mA), CH2 **M940L3** (940 nm), CH3 **M1050L4** (1050 nm,
  capped 600 mA), CH4 unused (reserved for a future 1300 nm LED). Use case:
  NIR imaging with an Arduino frame-sync trigger.

The example script and capability model also account for **SLC-MA04-MU /
CA04-MU** variants (which require an initialization step and support fan
control) **[V]**. Whether one of those is actually on hand is an open question —
the bench-verified unit is the SA04.

## 2. Physical connection & serial parameters

- RS232 ("-S") modules: 3-wire RS232 on DB9 female — pin 2 TXD, pin 3 RXD,
  pin 5 GND. Use a **straight-through** male-to-female cable, *not* a null
  modem cable. **[V]**
- **9600 baud, 8 data bits, no parity, 1 stop bit, no flow control**
  (9600, N, 8, 1). **[V]** Confirmed working with pyserial defaults and a
  **1.0 s read timeout**. **[HW]**
- Modules marked "X" have both USB and RS232 with a physical slide switch;
  power-cycle after switching. **[V]**
- **Decision: this library talks RS232/serial only.** **[C]** Background: the
  SDK states USB ("-U") modules enumerate as **HID devices**, driven via the
  vendor DLL (`Hiddll.dll`) — the docs never describe a virtual COM port for a
  module's own USB jack, so pyserial cannot drive that path. **[V]** Our SA04
  worked over a real serial path (`/dev/ttyUSB0` = the RS232 route via a
  USB-serial adapter). **[HW]** Consequence: any unit used with this library
  must expose an RS232 path — an "-S" unit, a dual-interface unit switched to
  RS232, or the DB9 through a USB-serial adapter. A USB-only hookup (e.g. an
  MA04-MU's front-panel USB jack) is out of scope by decision, not a problem
  to solve. The ASCII command set is identical over both pipes **[V]**, so
  nothing else in this document changes.

## 3. Command framing

- Commands are ASCII strings: `COMMAND DATA1 DATA2 … DATAn`, space-separated,
  **not case-sensitive**. **[V]**
- Commands are terminated with **LF+CR — `\n\r`, hex `0A 0D`, in that order**.
  This is *not* the conventional CRLF; getting it backwards is the classic
  failure mode. **[V][HW]**
- Responses are documented as `Response<SP><CR><LF>` **[V]**, but in practice
  responses carried mixed and trailing line-ending bytes. The proven read
  strategy: `read_until(b"\r")`, then wait **20 ms** and drain whatever else
  arrived, then decode ASCII (`errors="replace"`) and strip. **[HW]**
- The device transmits ASCII in both directions. **[V][HW]**

## 4. Response codes

One response per command, in both echo modes **[V]**:

| Response | Meaning | Proven check **[HW]** |
|---|---|---|
| `##` | Command valid, executed OK | substring: `"##" in response` |
| `#!` | Valid, executed, but an error occurred | `startswith("#!")` |
| `#?` | Valid command, argument out of range | `startswith("#?")` |
| `#<data>` | Valid, executed, data follows the `#` | strip `#`, parse |
| `[    xxxx is not defined]` | Unknown command | substring: `"is not defined"` |

Substring/prefix checks (not equality) are deliberate: they tolerate echo
remnants and stray line-ending bytes around the ack. **[HW]**

⚠ The SDK says that after `#!` the "Host can use 'Error' command to get the
Error code" — but no `Error` command or error-code table is defined anywhere
in the vendor documents. **[V, gap]** The contract reserves an optional `code`
field for this; treat it as unpopulated until proven otherwise.

## 5. Echo modes and PC Mode / initialization

- `ECHOON` echoes every received character plus a `>` prompt — terminal
  debugging only. `ECHOOFF` is the mode for host software, and is the default
  after any reset. **[V]**
- Send `ECHOOFF` immediately after opening the port, on every connect. The
  vendor recommends it, the vendor GUI does it, and on **MA04-MU / CA04-MU it
  is mandatory**: receiving `ECHOON` or `ECHOOFF` is what switches those
  modules from Manual Mode (knobs) into **PC Mode** (host control; knobs go
  dummy; the module outputs its last STOREd state on entry). **[V]**
- ⚠ `ECHOOFF` is **not acknowledged with `##`** — the real device returns
  *something* (never a clean ack), so send it, consume whatever comes back,
  and do not require an ack. **[HW]**
- This maps directly to the library's `requires_initialization` /
  `initialize()` concept: on MA/CA-MU variants initialization is the PC-Mode
  entry; on other modules the ECHOOFF is harmless hygiene. **[C]**

## 6. Command reference

Full command set **[V]**, annotated with what was actually exercised on real
hardware **[HW]**. Channel numbers (`ch`) are **one-based**, 1–4 on a
4-channel unit — in every command. Currents in mA (but see resolution, §8).

Commands the current slice's RS232 backend will eventually need are marked ★.

| | Command | Response | Notes |
|---|---|---|---|
| ★ | `ECHOOFF` / `ECHOON` | not `##`-acked **[HW]** | See §5. Send `ECHOOFF` on every connect. |
| ★ | `DEVICEINFO` | one line, `#`-prefixed info string | Our unit returns `Mightex LED Driver:3.1.8 Device Module No.:SLC-SA04-U/S Device Serial No.:04-251013-011` **[HW]**. The SDK's example (`PhotonEdge LED Driver:1.1.5 Device Serial No.:04-060510-001`) has a different shape and *no module field* — parse by keyword (`Driver:`, `Module No.:`, `Serial No.:`), never by position. **[V][HW]** |
| ★ | `MODE ch mode` | `##` | Set working mode: 0 DISABLE, 1 NORMAL, 2 STROBE, 3 TRIGGER. Takes effect immediately. Re-sending `MODE ch 2` while in STROBE restarts the profile. **[V][HW]** |
| ★ | `?MODE ch` | `#<mode>` e.g. `#1` | Query working mode. **[HW]** |
| ★ | `NORMAL ch Imax Iset` | `##` | Set NORMAL-mode params. `Imax` = per-mode programmable ceiling, `Iset` = working current. e.g. `NORMAL 1 200 100`. **[V][HW]** |
| ★ | `?CURRENT ch` | `#Cal1 Cal2 Imax Iset` e.g. `#50 60 200 100` | ⚠ First two fields are **calibration values — ignore them; take the last two tokens**. A positional parse reads calibration data as currents. **[V][HW]** |
| | `CURRENT ch Iset` | `##` | Quick-set working current, live. Only works while the channel is already in NORMAL mode. **[V][HW]** |
| | `STROBE ch Imax Repeat` | `##` | Strobe params. Profile plays `Repeat + 1` times; **9999 = repeat forever** (a reserved value *inside* the 0–99999999 range — exactly 10000 plays is impossible). **[V]** |
| | `STRP ch step Iset Tset` | `##` | Strobe profile step. `step` 0–127; `Tset` in µs; a `0 0` pair must terminate the profile (so 127 usable steps; **2 usable on SA/SV/FA/FV/HA/HV/MA/CA**). **[V]** |
| | `?STROBE ch` | `#Imax Repeat` | **[V]**, never exercised on hardware. |
| | `?STRP ch` | multi-line `#Iset Tset` pairs | **[V]**, never exercised on hardware. |
| | `TRIGGER ch Imax polarity` | `##` | Trigger params; polarity 0 rising, 1 falling. Not available on MA/CA. **[V][HW]** |
| | `TRIGP ch step Iset Tset` | `##` | Trigger profile step, same semantics as `STRP`. Special: **first step with `Tset` = 9999 makes the output follow the trigger input level** ("follower mode") at `Iset`. **[V][HW]** |
| | `?TRIGGER ch` | `#Imax polarity` e.g. `#1200 0` | **[HW]** |
| | `?TRIGP ch` | `#Iset Tset …` | ⚠ Response format is **unstable/undocumented** — the test project wrote a structured parser, deleted it, and retreated to substring matching. Treat as unverified territory. **[HW]** |
| | `LoadVoltage ch` | `#ch:mV` e.g. `#1:3200` | Mixed-case command. Voltage-monitoring ("V") modules only; the controller samples on a 20 ms interval, so meaningful in NORMAL or slow strobe only. Our SA04 has no voltage monitoring — expect failures; treat as best-effort. **[V][HW]** |
| | `STORE` | `##` | Persist *all* current volatile settings (all channels, all modes) to non-volatile memory. **[V][HW]** |
| | `RESET` | `##` | Soft reset. EchoOff is the default afterwards. **[V]** |
| | `RESTOREDEF` | `##` | Load factory defaults into the *volatile* settings only; follow with `STORE` to persist. **[V]** |
| | `FanPWM level` | `##` | MA04/CA04-MU only. `level` 0–10 = 0–100% in 10% steps. **[V]** |

## 7. Operating modes & state model

Four per-channel modes, integer codes **0 DISABLE, 1 NORMAL, 2 STROBE,
3 TRIGGER** — these integers are the device's own and appear on the wire in
`MODE`/`?MODE`; do not renumber. **[V][HW]**

- **Each channel holds an independent parameter set for every mode.**
  Configuring a mode (e.g. `NORMAL ch Imax Iset`) only stores parameters; it
  changes nothing physically until `MODE` selects that mode. This is the
  configure-then-activate model the library API mirrors. **[V]**
- **DISABLE (0):** channel fully off, zero output capability.
- **NORMAL (1):** continuous constant current at `Iset`, up to `Imax`.
  Entering NORMAL drives `Iset` immediately; `CURRENT` adjusts it live.
  ⚠ **There is no native "on for N ms" primitive** — timed-on must be
  host-timed (`MODE ch 1` … sleep … `MODE ch 0`), which is exactly what the
  current slice does, or emulated with a one-shot STROBE profile. **[V]**
- **STROBE (2):** programmed pattern of up to 127 usable `(mA, µs)` steps plus
  a repeat count; entering the mode starts the pattern; re-entering restarts
  it. Timing resolution 20 µs (100 µs on MA/CA, minimum step 1000 µs). **[V]**
- **TRIGGER (3):** like STROBE but armed on the external trigger edge.
  **Absent on MA and CA modules.** Opto-coupled input, 3.3–10 V source,
  ≥6 mA, max trigger delay 25 µs. **[V]**

**Persistence:** all settings are **volatile until `STORE`**. After a power
cycle the device reloads the last STOREd state and each channel *resumes its
stored mode immediately* (a channel stored in STROBE starts strobing at
power-on). Factory defaults: every channel DISABLE; NORMAL Imax 20 mA /
Iset 10 mA; STROBE and TRIGGER Imax 20 mA with empty profiles. The 20 mA
default is a deliberate safety floor. **[V]**

## 8. Limits, resolution, and safety

- Per-mode, per-channel programmable `Imax` is the primary LED-protection
  mechanism. Set it from the *LED's* datasheet, not the controller's ceiling —
  the SLC will happily overdrive an LED (pulsed modes allow 3.5 A on our SA04;
  our 1050 nm LED tops out at 600 mA). Validation must be per-LED. **[V][HW]**
- SA04 ceilings: **1000 mA NORMAL, 3500 mA STROBE/TRIGGER**. Values
  1001–3500 are valid only in pulsed modes. **[V][HW]**
- MA04-MU: 1200 mA in both NORMAL and STROBE; channel power limit stated as
  15 W in one place and 18 W in another (vendor contradiction). **[V]**
- **Current resolution by module family** — a driver must not hardcode 1 mA:
  AA/AV/SA/SV/HA/HV/MA: **1 mA** (value 100 = 100 mA); FA/FV/XA/XV:
  **0.1 mA** (value 100 = 10.0 mA); CA: **5 mA** (values quantized, e.g.
  123–127 → 125); QA: undocumented. **[V]**
- Profile constraints: step index 0–127, duration ≤ 99,999,999 µs, terminating
  `0 0` pair required. **[V][HW]**
- Module type integer codes (from the SDK header, the device's own
  numbering — load-bearing, never renumber): AA=0, AV=1, SA=2, SV=3, MA=4,
  CA=5, HA=6, HV=7, FA=8, FV=9, XA=10, XV=11, QA=12. **[V]**

## 9. Hardware-proven quirks (the goldmine)

Every item below was learned the hard way by the test project and verified on
the real device. The future RS232 backend must honor all of them. **[HW]**

1. **Asymmetric terminators.** Send `\n\r` (LF+CR); read until `\r`. See §3.
2. **Drain after the terminator.** The device sends trailing bytes after the
   first `\r` (stray `\n`, multi-part responses). Wait 20 ms after
   `read_until(b"\r")` and drain `in_waiting`, or leftovers poison the next
   command's response.
3. **`reset_input_buffer()` before every command.** Discards stale/echoed
   bytes from the previous exchange. Belt to the drain's suspenders.
4. **Ack by substring, error by prefix.** `"##" in response`;
   `startswith("#!")` / `startswith("#?")`; `"is not defined"` substring.
5. **`ECHOOFF` gets no `##` ack.** Send it, consume the response, move on.
6. **Strip `#` and tolerate junk in every parser.** All proven parsers do
   `response.replace("#", "")` then split — never positional parsing.
7. **`?CURRENT` leads with two calibration fields.** Take the *last two*
   tokens for `Imax`/`Iset`.
8. **~0.3 s settle between writing NORMAL params and reading them back.**
   An immediate `?CURRENT` after `NORMAL` returned stale values on real
   hardware. Mode round-trips need no such delay.
9. **`?TRIGP` response format varies.** A structured parser was written,
   tested, and abandoned for substring verification. Re-derive from hardware
   before trusting.
10. **Disable before reprogramming.** The proven trigger-follower sequence is
    `MODE ch 0` → `TRIGGER …` → `TRIGP …` (follower step, then `0 0`
    terminator) → `MODE ch 3`. Never reprogram parameters under an active
    mode.
11. **Program → verify → only then `STORE`.** Read settings back and compare
    before persisting; skip the store on any mismatch. Also: NV memory wears —
    don't `STORE` during experimentation.
12. **The device keeps driving LEDs after the serial port closes.** Nothing
    turns off automatically. Disable all channels in `finally` blocks; closing
    a connection is not a safety action.
13. **Timeouts surface as empty reads.** pyserial just returns fewer bytes;
    an entirely empty response after the 1.0 s timeout means "no response" —
    raise, don't retry blindly. (The proven stack had **no retries at all**
    and mostly worked; the buffer hygiene above is why.)
14. **Every command gets exactly one response** — the protocol is strictly
    request/reply at 9600 baud. **[V][HW]**

## 10. Open questions

Carried forward deliberately — answers require hardware or vendor contact:

1. ~~MA04-MU over its own USB port: HID or virtual COM?~~ **Closed by
   decision (2026-07-04):** the library is RS232/serial-only (§2), so the
   module-USB/HID question is moot for software. Residual: a purchasing
   constraint — future units must have an RS232 path.
2. **The `Error` command** referenced after `#!` is undefined in all vendor
   docs. Does it exist? What codes?
3. **`Iset > Imax` behavior** — clamp or `#?` rejection? Unspecified.
4. **MA04-MU channel power limit** — 15 W or 18 W (vendor contradiction).
5. **STROBE repeat semantics** — SDK says range 0–99999999 with 0 = play
   once; User Manual says 1–99999999. Both agree 9999 = forever.
6. **`DEVICEINFO` grammar** — only examples given, and they differ between
   documents and our real unit. Keyword parsing only.
7. **Which module families are 2-step-limited** — inferred, not enumerated,
   by the vendor.
8. **QA family current resolution** — undocumented.
9. **macOS serial behavior** — all hardware experience is Linux
   (`/dev/ttyUSB0`, `dialout` group); the `/dev/cu.*` path is untested.
