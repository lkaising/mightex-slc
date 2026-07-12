# mightex-slc

A Python library for driving Mightex Sirius SLC-series multi-channel LED
controllers over RS232. The current release covers **NORMAL-mode control**:
open the controller, store per-channel current parameters, switch a channel
on and off, and read back the live mode and stored parameters — verified on
real hardware (SLC-SA04-U/S, firmware 3.1.8).

## Quick start

```python
import time

from mightex_slc import NormalParameters, OperatingMode, open_device

with open_device(port="/dev/ttyUSB0") as controller:
    channel = controller.channel(1)                # one-based
    channel.set_normal_parameters(NormalParameters(current_max_ma=200.0, current_set_ma=100.0))
    channel.set_active_mode(OperatingMode.NORMAL)  # light on
    try:
        time.sleep(5.0)
    finally:
        channel.set_active_mode(OperatingMode.DISABLE)  # light off
```

No hardware attached? `open_fake_device()` opens a built-in simulated
controller; swap it in for the `open_device(...)` line and the rest runs
unchanged.

## Install

```
pip install -e .
```

Runtime dependencies: `pydantic`, `pyserial`. Python ≥ 3.12.

## Safety notes (real LEDs)

- **`Imax` is the LED's protection, not the controller's.** Set
  `current_max_ma` from the LED's own datasheet limit; the controller will
  happily overdrive a small LED.
- **Closing the port does not turn output off.** The device keeps driving its
  channels; always `set_active_mode(OperatingMode.DISABLE)` in a `finally`.
- Nothing in this library writes the controller's non-volatile memory.

More in [docs/using/safety.md](docs/using/safety.md).

## Documentation

- **[Getting started](docs/using/getting-started.md)** — first script,
  real vs. simulated device, finding your serial port.
- **[All documentation](docs/README.md)** — user guides, API reference,
  architecture, and the device protocol notes.
