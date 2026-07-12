# Safety Notes for Real LEDs

Four facts to internalize before driving real hardware.

## `Imax` is the LED's protection, not the controller's

Set `current_max_ma` from the **LED's own datasheet limit**, not from what
the controller allows. The controller's ceilings are far above what small
LEDs tolerate — an SA04 permits 1000 mA continuous and 3500 mA pulsed, which
will destroy an LED rated for a few hundred milliamps. Choose the limit
per LED, every time.

```python
# The LED's datasheet says 600 mA absolute maximum:
channel.set_normal_parameters(NormalParameters(current_max_ma=600.0, current_set_ma=300.0))
```

## Closing the port does not turn the output off

The device keeps driving its channels after the serial connection closes —
closing is **not** a safety action. Always disable in a `finally` block:

```python
try:
    channel.set_active_mode(OperatingMode.NORMAL)   # light on
    ...
finally:
    channel.set_active_mode(OperatingMode.DISABLE)  # light off, no matter what
```

## The device powers on into its last stored state

Nothing in this library writes the controller's non-volatile memory. But the
device itself reloads whatever was last persisted (with the vendor tools'
`STORE` command) on power-up, and each channel **resumes its stored mode
immediately** — a channel stored active starts driving at power-on. Know what
is stored in a unit before wiring an LED to it.

## Factory defaults are a deliberate safety floor

Fresh units default every channel to DISABLE with Imax 20 mA / Iset 10 mA,
precisely so an unconfigured channel cannot damage a load. Raising `Imax` is
the moment responsibility transfers to you.
