1. Tidy up the public facing docstring for the `set_trigger_parameters` and `set_trigger_profile` functions inside of `mightex-slc/src/mightex_slc/client/channel.py`.

2. Find a better home for the `FOLLOWER_SENTINEL_DURATION_US` constant or at least take out the comment. Tidy up the docstring for `StepProfile` and tighten the `ValueError` message. Tidy up the docstring for `FollowerProfile`. Look into if it is possible to validate `current_ma` against `current_max_ma` which is part of `TriggerParameters`. Think about whether it makes sense for 3 contract models to be living inside of the same file. Look into if the `_first_step_is_not_the_follower_sentinel` validation holds in the case of doing strobe mode. File of interest can be found here: `mightex-slc/src/mightex_slc/contract/components/profiles.py`.

3. Tidy up and tighten the docstring for `TriggerParameters` inside of `mightex-slc/src/mightex_slc/contract/components/trigger_parameters.py`.

4. Tidy up and tighten the docstring for `TriggerPolarity` inside of `mightex-slc/src/mightex_slc/contract/components/trigger_polarity.py`.

5. Same idea as point 2 where look into if it is possible to validate the `current_ma` arguement inside of `TriggerProfile` against the `current_max_ma` arguement inside of `TriggerParameters`. File is interest can be found here: `mightex-slc/src/mightex_slc/contract/operations/set_trigger_profile.py`.

6. Not the most happy with the `StepProfile` length validation inside of `set_trigger_profile`, it would be nice if this could be handle via `pydantic` but that might not be possible. The same idea follows for the `_require_trigger_support` function, would be nice if that could also be handled via `pydantic`. File of interest here is: `mightex-slc/src/mightex_slc/server/impl/channel.py`.

7. Not the most happy the implementation of the `encode_trigger_profile` function and its docstring should be tightened. Tighten the docstring inside of the `parse_trigger` function. Not the most happy with the implementation of the `parse_trigger_profile` function, also its docstring should be tightened. File of interest can be found here: `mightex-slc/src/mightex_slc/transport/rs232/codec.py`.

8. The docstrings inside of the fucntions `set_trigger_profile` and `get_trigger_profile` shoud be tightened. Inside of the `get_trigger_profile` function the function call to `exchange_multiline` feel more like a hack than anything. Not the most happy with that. The file of interest here is: `mightex-slc/src/mightex_slc/transport/rs232/rs232_transport.py`.

9. The most happy with the introduction of the `_QUIET_WINDOW_S`, `_QUIET_CAP_S`, and `_QUIET_POLL_S` constants, they also feel more like a hack than anything, will need to look into this. For these constants too, take out the comment block above. For the `exchange_multiline` function and the `_drain_until_quiet` helper, not the most happy with this, also feels like a hack. Would much rather have one unified exachange function. Also, the docstring inside of `exchange_multiline` needs to be tightened if preserved. File of intereset here is: `mightex-slc/src/mightex_slc/transport/rs232/serial_link.py`.
