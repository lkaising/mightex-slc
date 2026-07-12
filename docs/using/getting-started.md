# Getting Started

## Install

Requires Python ≥ 3.12. From the repository root:

```
pip install -e .
```

Runtime dependencies (`pydantic`, `pyserial`) install automatically.

## First script

Timed turn-on of one channel — configure the currents, switch the channel
on, and always switch it off in a `finally`:

```python
import time

from mightex_slc import NormalParameters, OperatingMode, open_device

with open_device(port="/dev/ttyUSB0") as controller:
    channel = controller.channel(1)  # channels are one-based

    # Store the NORMAL-mode currents. Output does not change yet.
    # current_max_ma is the LED's protection: take it from the LED datasheet.
    channel.set_normal_parameters(NormalParameters(current_max_ma=200.0, current_set_ma=100.0))
    print(channel.get_normal_parameters())   # read back what the device stored

    channel.set_active_mode(OperatingMode.NORMAL)  # light on
    try:
        time.sleep(5.0)
    finally:
        channel.set_active_mode(OperatingMode.DISABLE)  # light off

    print(channel.get_active_mode())          # OperatingMode.DISABLE
```

Before running this against a real LED, read [safety.md](safety.md) — in
particular why the `finally` is not optional and how to choose
`current_max_ma`.

## Real device or simulated device

Two ways to open a controller, each explicit — nothing is ever read from the
environment, and the simulated device is never selected implicitly:

- **Real hardware:** `open_device(port="/dev/ttyUSB0")`. The port is always
  the one you name; omitting it raises `ValueError`.
- **No hardware:** `open_fake_device()` opens a built-in simulated 4-channel
  controller. Swap the `open_device(port=...)` line for it and the script
  above runs as-is, which makes the fake the natural way to develop and
  test. Details of what it simulates are in
  [api.md](api.md#open_fake_device---controller).

For tests and custom integrations, `open_device(transport=...)` accepts any
transport implementation — see [api.md](api.md#custom-transports).

## Finding your serial port

The library never scans or probes serial ports (opening a port is a
side-effecting act on this hardware), so you always name the port yourself.

On Linux, a USB-serial adapter typically appears as `/dev/ttyUSB0`:

```
$ ls /dev/ttyUSB*
/dev/ttyUSB0
```

With several candidates, `ls -l /dev/serial/by-id/` names each port by its
adapter. Your user needs permission to open it — on most distributions that
means membership in the `dialout` group:

```
$ sudo usermod -a -G dialout $USER   # then log out and back in
```

Hardware use of this library to date has been on Linux. On other platforms
the port follows the OS convention (`COM3` on Windows, `/dev/cu.usbserial-*`
on macOS), but those paths are unexercised.

Which units the library supports and how to cable them: [devices.md](devices.md).

## Next steps

- [safety.md](safety.md) — the four rules for driving real LEDs.
- [devices.md](devices.md) — supported SLC controllers and their limits.
- [api.md](api.md) — the complete public API.
