# TODO

Personal follow-up notes for reviewing and refining the TRIGGER-mode
implementation.

## Public client API

- [ ] Tidy and tighten the public-facing docstrings for
  `Channel.set_trigger_parameters()` and `Channel.set_trigger_profile()`.
  - File: `src/mightex_slc/client/channel.py`

## Contract models and operations

- [ ] Revisit the profile contract models and their organization.
  - Find a better home for `FOLLOWER_SENTINEL_DURATION_US`, or at minimum
    remove the comment above it.
  - Tighten the `StepProfile` docstring and its `ValueError` message.
  - Tighten the `FollowerProfile` docstring.
  - Look into whether `current_ma` can be validated against
    `TriggerParameters.current_max_ma`.
  - Think about whether it makes sense for all three contract models to live
    in the same file.
  - Check whether `_first_step_is_not_the_follower_sentinel` remains valid
    when `StepProfile` is used for STROBE mode.
  - File: `src/mightex_slc/contract/components/profiles.py`

- [ ] Tighten the `TriggerParameters` docstring.
  - File: `src/mightex_slc/contract/components/trigger_parameters.py`

- [ ] Tighten the `TriggerPolarity` docstring.
  - File: `src/mightex_slc/contract/components/trigger_polarity.py`

- [ ] Following the related question in `profiles.py`, look into whether the
  `current_ma` value in a `TriggerProfile` can be validated against
  `TriggerParameters.current_max_ma` as part of the `set_trigger_profile`
  operation.
  - File: `src/mightex_slc/contract/operations/set_trigger_profile.py`

## Server policy

- [ ] I am not fully satisfied with the `StepProfile` length validation in
  `ChannelModel.set_trigger_profile()`.
  - I would prefer Pydantic to handle this validation if feasible, although
    that may not be possible.
  - The same preference applies to `_require_trigger_support()`: look into
    whether Pydantic can handle it instead.
  - File: `src/mightex_slc/server/impl/channel.py`

## RS232 codec

- [ ] I am not fully satisfied with parts of the trigger-profile encoding and
  parsing implementation.
  - Revisit `encode_trigger_profile()` and tighten its docstring.
  - Tighten the `parse_trigger()` docstring.
  - Revisit `parse_trigger_profile()` and tighten its docstring.
  - File: `src/mightex_slc/transport/rs232/codec.py`

## RS232 transport

- [ ] Tighten the docstrings for `set_trigger_profile()` and
  `get_trigger_profile()`.
  - I am not fully satisfied with the direct use of `exchange_multiline()`
    inside `get_trigger_profile()`; it feels more like a workaround than a
    clean design.
  - File: `src/mightex_slc/transport/rs232/rs232_transport.py`

## Serial link

- [ ] I am not fully satisfied with the multiline exchange mechanism; parts
  of it feel more like a workaround than a clean design.
  - Revisit the introduction of `_QUIET_WINDOW_S`, `_QUIET_CAP_S`, and
    `_QUIET_POLL_S`.
  - Remove the comment block above those constants.
  - Reconsider `exchange_multiline()` and `_drain_until_quiet()`.
  - I would strongly prefer a single, unified exchange function that supports
    both ordinary and multiline responses.
  - Tighten the `exchange_multiline()` docstring if the function is retained.
  - File: `src/mightex_slc/transport/rs232/serial_link.py`
