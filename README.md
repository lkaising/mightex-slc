# mightex-slc

A Python library for driving Mightex Sirius SLC multi-channel LED controllers
over RS232, built as vertical slices. The current slice is **NORMAL-mode
timed turn-on**: open the controller, store per-channel current parameters,
switch the channel on, switch it off, close.

Verified on real hardware (SLC-SA04-U/S, firmware 3.1.8) on 2026-07-06.

## Quick start

```python
import time

from mightex_slc import OperatingMode, open_device

with open_device(port="/dev/ttyUSB0") as controller:
    channel = controller.channel(1)                # one-based
    channel.configure_normal(current_max_ma=200.0, current_set_ma=100.0)
    channel.set_active_mode(OperatingMode.NORMAL)  # light on
    try:
        time.sleep(5.0)
    finally:
        channel.set_active_mode(OperatingMode.DISABLE)  # light off
```

A runnable version lives at `../examples/normal_mode_timed_on.py`.

## Install

```
pip install -e .
```

Runtime dependencies: `pydantic`, `pyserial`. Python ≥ 3.11.

## Backend selection

Two transports sit behind one interface:

- **rs232** (default) — the real serial backend. The port is the one you name:
  pass it to `open_device(port=...)`, or set `MIGHTEX_SLC_PORT` as the default.
  The library never scans or probes serial ports.
- **fake** — an in-memory simulated controller for development and tests.
  Select it with `MIGHTEX_SLC_BACKEND=fake`.

## Safety notes (real LEDs)

- **`Imax` is the LED's protection, not the controller's.** Set
  `current_max_ma` from the LED's own datasheet limit; the controller will
  happily overdrive a small LED.
- **Closing the port does not turn output off.** The device keeps driving its
  channels; always `set_active_mode(OperatingMode.DISABLE)` in a `finally`.
- Nothing in this library writes the controller's non-volatile memory.

## Layout

- `src/mightex_slc/` — the library: `contract/` (Pydantic seam models),
  `client/` (public proxies), `server/` (dispatch, session, device models),
  `transport/` (the fake and rs232 backends behind one interface).
- `docs/` — sorted by trust: `vendor/` (authoritative protocol),
  `reference/` (design + hardware-verified protocol digest), `handoff/`,
  `stale/` (history; do not trust literally).
- `schemas/` — generated documentation artifacts
  (`python scripts/generate_schemas.py`); never hand-edited.
- Tests and hardware bring-up probes live in the sibling `../examples/`
  project, not in this package:
  `cd ../examples && .venv/bin/python -m pytest tests -q`.
