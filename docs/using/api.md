# API Reference

The public API is everything importable from the top-level package:

```python
from mightex_slc import (
    open_device, open_fake_device,          # entry points
    Controller, Channel,                    # proxies
    NormalParameters, OperatingMode,        # models
    ControllerCapabilities, ModuleType,
    MightexLEDError, DeviceConnectionError, # exceptions
    DeviceNotFoundError, DeviceCommandError,
    UnsupportedOperationError, ControllerClosedError,
)
```

If a name is not importable from `mightex_slc`, it is not part of the public
API (with one documented exception: the `Transport` interface for custom
transports, [below](#custom-transports)).

---

## Opening a device

### `open_device(port=None, *, transport=None) -> Controller`

Open a controller and return a proxy for it.

- `port` — serial port path of the controller, such as `"/dev/ttyUSB0"`.
- `transport` — optional transport implementation for tests or custom
  integrations; `port` is forwarded to it.

Raises `ValueError` if neither `port` nor `transport` is given,
`DeviceNotFoundError` if nothing responds at the requested port, and
`DeviceConnectionError` if the connection fails for another reason.

Opening is **side-effecting**: it sends `ECHOOFF` to enter host control
(on MA04-MU / CA04-MU units this switches the module from knob control into
PC Mode, where it outputs its last stored state). There is no separate
initialization step. On POSIX the serial port is opened with exclusive
ownership, so a second open of the same port fails as a connection error.

The library never scans or probes serial ports; you always name the port.
Nothing is read from the environment.

### `open_fake_device() -> Controller`

Open the built-in simulated controller — the explicit no-hardware path,
never selected implicitly. Equivalent to `open_device(transport=FakeTransport())`.

The fake simulates a single **SLC-MA04-MU**:

- 4 channels, 1 mA current resolution, current range 0–1200 mA
  (values outside it are rejected as `DeviceCommandError`).
- No TRIGGER mode — `set_active_mode(OperatingMode.TRIGGER)` raises
  `DeviceCommandError`, which keeps the no-trigger capability path
  exercisable without hardware.
- Reports `supports_fan_control=True` (an MA04-MU trait), no load-voltage
  read-back, `max_profile_steps=2`.
- Every channel starts at the documented factory defaults: mode `DISABLE`,
  NORMAL Imax 20 mA / Iset 10 mA.
- Channel state persists after `close()` — a real controller keeps driving
  its outputs when the serial port closes, and the fake mirrors that.
- `restore_factory_defaults()` resets every channel to the factory defaults;
  `persist_settings()` acknowledges and changes nothing observable — the
  fake does not model power cycles.

## `Controller`

An opened controller, returned by the open functions — never constructed
directly. Also a context manager: `with open_device(...) as controller:`
closes it on exit.

| Member | Description |
|---|---|
| `device_id: str` | Opaque identifier minted for this open session. |
| `capabilities: ControllerCapabilities` | The device's reported capabilities, cached at open — reading it costs no round trip. |
| `is_closed: bool` | Whether `close()` has been called. |
| `channel(number: int) -> Channel` | Proxy for one channel. `number` is **one-based**, from 1 through `capabilities.channel_count`. Constructing the proxy is pure client-side work; an out-of-range number is rejected by the device on the first operation, as `DeviceCommandError`. |
| `persist_settings() -> None` | Persist the current settings of all channels and modes to non-volatile memory — the state the device reloads at power-on. Output is unchanged. **NV memory wears**: verify settings first, persist deliberately — see [safety.md](safety.md). |
| `restore_factory_defaults() -> None` | Load factory defaults (every channel `DISABLE`, NORMAL Imax 20 mA / Iset 10 mA) into the current **volatile** settings, **effective immediately** — a driving channel turns off. Persists nothing; follow with `persist_settings()` to keep the defaults across power cycles. |
| `close() -> None` | Close the controller and release the device connection. Idempotent. **Not a safety action**: the device keeps driving its channels after close — see [safety.md](safety.md). |

Operations on a closed controller (or its channels) raise
`ControllerClosedError`.

## `Channel`

A proxy for one channel of an open controller, obtained from
`controller.channel(n)`. It holds no device state; each method is one
round trip to the device.

The device follows a **configure-then-activate** model: parameters are stored
per mode and change nothing physically until the mode is made active.

| Method | Description |
|---|---|
| `set_normal_parameters(parameters: NormalParameters) -> None` | Store NORMAL-mode current parameters for this channel. **Output is unchanged** until NORMAL mode is activated. |
| `get_normal_parameters() -> NormalParameters` | Read back the stored NORMAL-mode parameter pair. |
| `set_active_mode(mode: OperatingMode) -> None` | Switch the channel's working mode, **effective immediately**: `NORMAL` starts driving the stored set current; `DISABLE` turns the channel off. |
| `get_active_mode() -> OperatingMode` | Read back the mode currently driving the channel. |

`Channel` also exposes `device_id: str` and `number: int` as read-only
properties.

## Models

### `NormalParameters`

The NORMAL-mode current parameter pair for one channel. Immutable
(construct a new one to change values).

| Field | Description |
|---|---|
| `current_max_ma: float` | NORMAL-mode current limit, in mA. **This is the LED's protection** — set it from the LED's datasheet ([safety.md](safety.md)). |
| `current_set_ma: float` | NORMAL-mode set current, in mA — what flows when the channel enters NORMAL mode. |

Validation at construction (violations raise `ValueError` /
`pydantic.ValidationError` before anything reaches the device): both values
must be ≥ 0, and `current_set_ma` must not exceed `current_max_ma`.

The values are never rescaled or rounded. The RS232 backend serializes whole
milliamps only: a non-integral value such as `100.5` is refused as
`DeviceCommandError` rather than silently rounded.

### `OperatingMode`

An `IntEnum` of the four per-channel working modes. The values are the
device's own wire codes — do not renumber.

| Member | Value | Meaning |
|---|---|---|
| `DISABLE` | 0 | Channel fully off. |
| `NORMAL` | 1 | Continuous constant current at the stored set current. |
| `STROBE` | 2 | Programmed current/time pattern. |
| `TRIGGER` | 3 | Pattern armed on the external trigger edge. Not available on MA/CA modules. |

The current release configures NORMAL mode only; `STROBE`/`TRIGGER` can be
activated with `set_active_mode`, but no API sets their parameters yet.

### `ControllerCapabilities`

Read-only limits and feature flags reported by the device at open, available
as `controller.capabilities`.

| Field | Description |
|---|---|
| `module_type: ModuleType` | Controller module family. |
| `channel_count: int` | Number of LED output channels (≥ 1). |
| `current_resolution_ma: float` | Smallest settable current increment, in mA (1 mA on most families; 5 mA on CA). |
| `max_profile_steps: int` | Maximum programmable current/time pairs (2–127) before the required (0, 0) terminator. |
| `supports_trigger_mode: bool` | Whether TRIGGER mode is available. |
| `supports_load_voltage: bool` | Whether load-voltage read-back is available. |
| `supports_fan_control: bool` | Whether FanPWM control is available. |

### `ModuleType`

An `IntEnum` of module families, using the vendor SDK's own integer codes
(load-bearing — never renumber): `AA=0, AV=1, SA=2, SV=3, MA=4, CA=5, HA=6,
HV=7, FA=8, FV=9, XA=10, XV=11, QA=12`. See
[devices.md](devices.md) for which families the library supports.

## Errors

```
MightexLEDError                  base of every library-raised operation error
├── DeviceConnectionError        connection cannot be established or maintained
│   └── DeviceNotFoundError      nothing responds at the requested serial target
├── DeviceCommandError           the device rejected a command (carries .code)
├── UnsupportedOperationError    the operation is not supported
└── ControllerClosedError        operation on a closed controller handle
```

- **Bad arguments raise plain `ValueError`, deliberately outside this tree**
  — invalid values (negative currents, set > max, channel < 1, an invalid
  mode) fail validation client-side, before anything reaches the device.
- `DeviceCommandError` covers device-side refusals: out-of-range channel
  numbers, currents the module rejects, modes the module lacks (e.g. TRIGGER
  on MA/CA), and values the wire cannot express (non-whole mA). Its `code`
  attribute is reserved for a device-reported error code and is **currently
  always `None`** — the device reports execution failure as a single
  undifferentiated condition.
- `DeviceConnectionError` covers serial I/O failures and timeouts after the
  connection was established; `DeviceNotFoundError` means the open itself
  found nothing (port missing, no response to identification).
- `ControllerClosedError` is raised for any operation through a closed
  `Controller` or its `Channel` proxies.

## Custom transports

`open_device(transport=...)` accepts any implementation of the transport
interface — this is how tests run the full client → server stack over a
simulated device, and how a custom integration could slot in. The interface
lives one level below the top-level package:

```python
from mightex_slc.transport import Transport, FakeTransport, RS232Transport
```

`Transport` is the abstract interface; `FakeTransport` is the simulated
controller behind `open_fake_device()`; `RS232Transport` is the real serial
backend that `open_device(port=...)` constructs by default (it accepts
`baudrate` and `timeout` keyword overrides). When a transport is injected,
`port` is forwarded to it — the fake accepts and ignores it, while
`RS232Transport` requires it.
