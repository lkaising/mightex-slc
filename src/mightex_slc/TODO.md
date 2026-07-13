1. Tidy up the public facing docstring for the `set_trigger_parameters` and `set_trigger_profile` functions inside of `mightex-slc/src/mightex_slc/client/channel.py`.

2. Find a better home for the `FOLLOWER_SENTINEL_DURATION_US` constant or at least take out the comment. Tidy up the docstring for `StepProfile` and tighten the `ValueError` message. Tidy up the docstring for `FollowerProfile`. Look into if it is possible to validate `current_ma` against `current_max_ma` which is part of `TriggerParameters`. Think about whether it makes sense for 3 contract models to be living inside of the same file. Look into if the `_first_step_is_not_the_follower_sentinel` validation holds in the case of doing strobe mode. File of interest can be found here: `mightex-slc/src/mightex_slc/contract/components/profiles.py`.

3. Tidy up and tighten the docstring for `TriggerParameters` inside of `mightex-slc/src/mightex_slc/contract/components/trigger_parameters.py`.

4. Tidy up and tighten the docstring for `TriggerPolarity` inside of `mightex-slc/src/mightex_slc/contract/components/trigger_polarity.py`.

5. Same idea as point 2 where look into if it is possible to validate the `current_ma` arguement inside of `TriggerProfile` against the `current_max_ma` arguement inside of `TriggerParameters`. File is interest can be found here: `mightex-slc/src/mightex_slc/contract/operations/set_trigger_profile.py`.
