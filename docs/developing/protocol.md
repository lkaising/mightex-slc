# Device and Protocol Reference

Everything the library knows about Mightex SLC-series LED controllers and
their ASCII wire protocol: the vendor-documented command set, plus the
behavior actually observed on real hardware.

Every claim carries a provenance tag:

- **[V]** — stated in the vendor documents.
- **[HW]** — verified on a real device.
- **[C]** — a library convention, chosen by this project.

Tags combine where a fact is both documented and hardware-confirmed
(**[V][HW]**). **[V, gap]** marks a vendor-documented feature with no
supporting specification. Anything untagged should be treated as unverified.

Unless a date says otherwise, all **[HW]** claims were verified on a
**Mightex SLC-SA04-U/S** (4-channel SA family, firmware **3.1.8**), connected
at `/dev/ttyUSB0` on Linux through an FTDI FT232R USB-serial adapter, during
the July 2026 bring-up of the RS232 backend.

Vendor sources — converted to markdown in-repo at [`../vendor/`](../vendor/):

- [*SDK Description* v1.1.4 (2018)](../vendor/mightex_sirius_multi_channel_led_controller_sdk_description.md)
  — the authoritative command set.
- [*User Manual* v1.3.6 (2018)](../vendor/mightex_sirius_multi_channel_led_controller_user_manual.md)
  — modes, module matrix, electrical limits, safety, MA04-MU §3.0.

---

## 1. Physical connection and serial parameters

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
  module's own USB jack, so pyserial cannot drive that path. **[V]** The bench
  unit worked over a real serial path (`/dev/ttyUSB0` = the RS232 route via a
  USB-serial adapter). **[HW]** Consequence: any unit used with this library
  must expose an RS232 path — an "-S" unit, a dual-interface unit switched to
  RS232, or the DB9 through a USB-serial adapter. A USB-only hookup (e.g. an
  MA04-MU's front-panel USB jack) is out of scope by decision, not a problem
  to solve. The ASCII command set is identical over both pipes **[V]**, so
  nothing else in this document changes.

## 2. Command framing

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

The library implements this line discipline in
`src/mightex_slc/transport/rs232/serial_link.py`; the command and response
strings live in `src/mightex_slc/transport/rs232/codec.py`.

## 3. Response codes

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

## 4. Echo modes and PC Mode

- `ECHOON` echoes every received character plus a `>` prompt — terminal
  debugging only. `ECHOOFF` is the mode for host software, and is the default
  after any reset. **[V]**
- Send `ECHOOFF` immediately after opening the port, on every connect. The
  vendor recommends it, the vendor GUI does it, and on **MA04-MU / CA04-MU it
  is mandatory**: receiving `ECHOON` or `ECHOOFF` is what switches those
  modules from Manual Mode (knobs) into **PC Mode** (host control; knobs go
  dummy; the module outputs its last STOREd state on entry). **[V]**
- ⚠ Do **not require an ack** for `ECHOOFF`: send it, consume whatever comes
  back, move on. History recorded it as never cleanly acked **[HW]**, but on
  2026-07-06 the bench SA04 (fw 3.1.8, already in EchoOff state) answered a
  clean `## \r\n` — the reply evidently varies with state/firmware, which is
  exactly why the no-ack-required rule stands. **[HW]**
- In the library, ECHOOFF is folded into `open_device` — opening the port IS
  the host-control entry (PC-Mode entry on MA/CA-MU variants; harmless
  hygiene elsewhere). There is no separate initialization step. **[C]**

## 5. Command reference

Full command set **[V]**, annotated with what was actually exercised on real
hardware **[HW]**. Channel numbers (`ch`) are **one-based**, 1–4 on a
4-channel unit — in every command. Currents in mA (but see resolution, §7).

The six commands the library sends today are marked ●; the rest are documented
for future slices.

| | Command | Response | Notes |
|---|---|---|---|
| ● | `ECHOOFF` / `ECHOON` | not `##`-acked **[HW]** | See §4. Send `ECHOOFF` on every connect. |
| ● | `DEVICEINFO` | one line, **bare** (no `#` prefix) string | The bench unit returns `Mightex LED Driver:3.1.8 Device Module No.:SLC-SA04-U/S Device Serial No.:04-251013-011` — raw framing observed 2026-07-06: `…011 \r\n` (trailing space, then CR LF) **[HW]**. The SDK's example (`PhotonEdge LED Driver:1.1.5 Device Serial No.:04-060510-001`) has a different shape and *no module field* — parse by keyword (`Driver:`, `Module No.:`, `Serial No.:`), never by position. **[V][HW]** |
| ● | `MODE ch mode` | `##` | Set working mode: 0 DISABLE, 1 NORMAL, 2 STROBE, 3 TRIGGER. Takes effect immediately. Re-sending `MODE ch 2` while in STROBE restarts the profile. **[V][HW]** |
| ● | `?MODE ch` | `#<mode>` e.g. `#1` | Query working mode. **[HW]** |
| ● | `NORMAL ch Imax Iset` | `##` | Set NORMAL-mode params. `Imax` = per-mode programmable ceiling, `Iset` = working current. e.g. `NORMAL 1 200 100`. **[V][HW]** |
| ● | `?CURRENT ch` | `#<calibration…> Imax Iset` | ⚠ The vendor documents two leading calibration fields (`#Cal1 Cal2 Imax Iset`); fw 3.1.8 actually returns **twelve fields**, e.g. `#5 81 480 972 1468 1964 8 -72 8000 0 1000 10` (2026-07-06; one field can be negative). `Imax`/`Iset` are the **last two tokens** — that rule, not any positional count, is the parse. **[V][HW]** |
| | `CURRENT ch Iset` | `##` | Quick-set working current, live. Only works while the channel is already in NORMAL mode. **[V][HW]** |
| | `STROBE ch Imax Repeat` | `##` | Strobe params. Profile plays `Repeat + 1` times; **9999 = repeat forever** (a reserved value *inside* the 0–99999999 range — exactly 10000 plays is impossible). **[V]** |
| | `STRP ch step Iset Tset` | `##` | Strobe profile step. `step` 0–127; `Tset` in µs; a `0 0` pair must terminate the profile (so 127 usable steps; **2 usable on SA/SV/FA/FV/HA/HV/MA/CA**). **[V]** |
| | `?STROBE ch` | `#Imax Repeat` | **[V]**, never exercised on hardware. |
| | `?STRP ch` | multi-line `#Iset Tset` pairs | **[V]**, never exercised on hardware. |
| | `TRIGGER ch Imax polarity` | `##` | Trigger params; polarity 0 rising, 1 falling. Not available on MA/CA. **[V][HW]** |
| | `TRIGP ch step Iset Tset` | `##` | Trigger profile step, same semantics as `STRP`. Special: **first step with `Tset` = 9999 makes the output follow the trigger input level** ("follower mode") at `Iset`. **[V][HW]** |
| | `?TRIGGER ch` | `#Imax polarity` e.g. `#1200 0` | **[HW]** |
| | `?TRIGP ch` | `#Iset Tset …` | ⚠ Response format is **unstable/undocumented** — a structured parser was written, tested, and abandoned for substring matching. Treat as unverified territory. **[HW]** |
| | `LoadVoltage ch` | `#ch:mV` e.g. `#1:3200` | Mixed-case command. Voltage-monitoring ("V") modules only; the controller samples on a 20 ms interval, so meaningful in NORMAL or slow strobe only. Non-"V" modules (like the bench SA04) have no voltage monitoring — expect failures; treat as best-effort. **[V][HW]** |
| | `STORE` | `##` | Persist *all* current volatile settings (all channels, all modes) to non-volatile memory. **[V][HW]** |
| | `RESET` | `##` | Soft reset. EchoOff is the default afterwards. **[V]** |
| | `RESTOREDEF` | `##` | Load factory defaults into the *volatile* settings only; follow with `STORE` to persist. **[V]** |
| | `FanPWM level` | `##` | MA04/CA04-MU only. `level` 0–10 = 0–100% in 10% steps. **[V]** |

## 6. Operating modes and state model

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
  library's NORMAL-mode slice does, or emulated with a one-shot STROBE
  profile. **[V]**
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

## 7. Limits, resolution, and safety

- Per-mode, per-channel programmable `Imax` is the primary LED-protection
  mechanism. Set it from the *LED's* datasheet, not the controller's ceiling —
  the SLC will happily overdrive an LED (an SA04 allows 3.5 A in pulsed modes;
  many small LEDs tolerate a fraction of that). Validation must be per-LED.
  **[V][HW]**
- Per-family current ceilings (NORMAL / STROBE-TRIGGER), from the vendor
  module matrix **[V]**:

  | Family | NORMAL ceiling | Pulsed ceiling |
  |---|---|---|
  | AA / AV | 1000 mA | 3500 mA |
  | SA / SV | 1000 mA | 3500 mA — confirmed on the bench SA04 **[HW]** |
  | HA / HV | 2000 mA | 3500 mA |
  | MA / CA | 1000 mA (1200 mA on -MU variants) | same as NORMAL (no TRIGGER) |
  | FA / FV / XA / XV | 100 mA | 350 mA |

  Values between the NORMAL and pulsed ceilings are valid only in pulsed
  modes. **[V][HW]** MA04-MU channel power limit is stated as 15 W in one
  place and 18 W in another (vendor contradiction). **[V]**
- **Current resolution by module family** — a driver must not hardcode 1 mA:
  AA/AV/SA/SV/HA/HV/MA: **1 mA** (value 100 = 100 mA); FA/FV/XA/XV:
  **0.1 mA** (value 100 = 10.0 mA); CA: **5 mA** (values quantized, e.g.
  123–127 → 125); QA: undocumented. **[V]**
- Profile constraints: step index 0–127, duration ≤ 99,999,999 µs, terminating
  `0 0` pair required. **[V][HW]**
- Module type integer codes (from the SDK header, the device's own
  numbering — load-bearing, never renumber): AA=0, AV=1, SA=2, SV=3, MA=4,
  CA=5, HA=6, HV=7, FA=8, FV=9, XA=10, XV=11, QA=12. **[V]**

## 8. Hardware-proven quirks

Every item below was learned the hard way and verified on the real device.
The RS232 backend honors all of them. **[HW]**

1. **Asymmetric terminators.** Send `\n\r` (LF+CR); read until `\r`. See §2.
2. **Drain after the terminator.** The device sends trailing bytes after the
   first `\r` (stray `\n`, multi-part responses). Wait 20 ms after
   `read_until(b"\r")` and drain `in_waiting`, or leftovers poison the next
   command's response.
3. **`reset_input_buffer()` before every command.** Discards stale/echoed
   bytes from the previous exchange. Belt to the drain's suspenders.
4. **Ack by substring, error by prefix.** `"##" in response`;
   `startswith("#!")` / `startswith("#?")`; `"is not defined"` substring.
5. **Never require an ack for `ECHOOFF`.** Send it, consume the response,
   move on. (Historically it was never cleanly acked; on 2026-07-06 the SA04
   answered a clean `## \r\n` — the reply varies, the rule holds.)
6. **Strip `#` and tolerate junk in every parser.** All proven parsers do
   `response.replace("#", "")` then split — never positional parsing.
7. **`?CURRENT` leads with calibration fields — more than documented.** The
   vendor says two; fw 3.1.8 returns ten before the currents (twelve fields
   total, observed 2026-07-06). Take the *last two* tokens for `Imax`/`Iset`.
8. **The historical ~0.3 s post-write settle is cleared.** An earlier driver
   saw stale values from an immediate `?CURRENT` after `NORMAL`; on
   2026-07-11 a bench probe (one SA04, fw 3.1.8, channel 1; 50 alternating
   write/read rounds) read every write back fresh immediately under the
   per-command reset + drain recipe. The staleness is attributed to that
   earlier driver's weaker buffer hygiene, not firmware lag; this library
   adds no delay. Mode round-trips never needed one.
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

## 9. Unresolved protocol questions

Carried deliberately — answers require hardware or vendor contact. Do not
"resolve" these from memory:

1. **The `Error` command** referenced after `#!` is undefined in all vendor
   docs. Does it exist? What codes?
2. **`Iset > Imax` behavior** — clamp or `#?` rejection? Unspecified. (The
   library's `NormalParameters` refuses the combination at construction, so
   the device's behavior never has to be known.)
3. **MA04-MU channel power limit** — 15 W or 18 W (vendor contradiction).
4. **STROBE repeat semantics** — SDK says range 0–99999999 with 0 = play
   once; User Manual says 1–99999999. Both agree 9999 = forever.
5. **`DEVICEINFO` grammar** — only examples given, and they differ between
   documents and the real unit. Keyword parsing only.
6. **Which module families are 2-step-limited** — inferred, not enumerated,
   by the vendor.
7. **QA family current resolution** — undocumented.
8. **Non-Linux serial behavior** — all hardware experience is Linux
   (`/dev/ttyUSB0`, `dialout` group); macOS and Windows serial paths are
   unexercised.
