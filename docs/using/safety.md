# Safety Notes for Real LEDs

Five facts to internalize before driving real hardware.

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

## Trigger configuration is never rejected — verify it, and reprogram disabled

The device acknowledges every trigger-configuration command, even ones it
silently altered: an over-ceiling TRIGGER limit is clamped, and profile step
currents above the stored limit are clamped at write time. When the stored
values protect an LED, read them back and compare before arming:

```python
channel.set_trigger_parameters(intended)
assert channel.get_trigger_parameters() == intended   # ack is not verify
```

The device also silently accepts reprogramming while a channel is armed, and
what that does to an executing profile is untested. Disable first, configure,
verify, then arm — the full sequence is in [api.md](api.md#trigger-configuration-workflow).

## The device powers on into its last stored state

This library writes the controller's non-volatile memory only through the
explicit `persist_settings()` call (the device's `STORE` command); nothing
persists as a side effect of any other operation. The device reloads whatever
was last persisted on power-up, and each channel **resumes its stored mode
immediately** — a channel stored active starts driving at power-on. Know what
is stored in a unit before wiring an LED to it. Non-volatile memory also
wears with repeated writes: verify settings first, then persist deliberately,
not on every iteration of an experiment.

## Factory defaults are a deliberate safety floor

Fresh units default every channel to DISABLE with Imax 20 mA / Iset 10 mA,
precisely so an unconfigured channel cannot damage a load. Raising `Imax` is
the moment responsibility transfers to you.

`restore_factory_defaults()` returns the current (volatile) settings to this
floor **effective immediately** — a driving channel turns off — without
persisting anything; follow it with `persist_settings()` to make the floor
the power-on state.
