# Changelog

## Ongoing

- Test/validate for Python 3.14

## v1.7.8

- Implement fixes related to the select-platform-data provided to the HA Core integrations, part of solving pw-beta issue [#897](https://github.com/plugwise/plugwise-beta/issues/897)
- Chores move module publishing on (test)pypi to Trusted Publishing (and using uv)

## v1.7.7

- Implement code quality improvements as suggested by SonarCloud via [#762](https://github.com/plugwise/python-plugwise/pull/762), [#763](https://github.com/plugwise/python-plugwise/pull/763), [#764](https://github.com/plugwise/python-plugwise/pull/764), and [#765](https://github.com/plugwise/python-plugwise/pull/765)

## v1.7.6

- Maintenance chores (mostly reworking Github CI Actions) backporting from efforts on Python Plugwise [USB: #264](https://github.com/plugwise/python-plugwise-usb/pull/264) after porting our progress using [USB: #263](https://github.com/plugwise/python-plugwise-usb/pull/263)
- Don't raise an error when a locked switch is being toggled, and other switch-related improvements via [#755](https://github.com/plugwise/python-plugwise/pull/755)

## v1.7.5

- Maintenance chores
- Deprecating python 3.12

## v1.7.4

- Maintenance chores

## v1.7.3

- Improve readability of xml-data in POST/PUT requests via [#707](https://github.com/plugwise/python-plugwise/pull/707), [#708](https://github.com/plugwise/python-plugwise/pull/708) and [#715](https://github.com/plugwise/python-plugwise/pull/715)
- Continuous improvements via [#711](https://github.com/plugwise/python-plugwise/pull/711), [#713](https://github.com/plugwise/python-plugwise/pull/713) and [#716](https://github.com/plugwise/python-plugwise/pull/716)

## v1.7.2

- Bugfix for Plugwise-beta issue [833](https://github.com/plugwise/plugwise-beta/issues/833) solving relay- and lock-switches not switching for the Stretch.

## v1.7.1

- Avoid None-init for smile_version [#699](https://github.com/plugwise/python-plugwise/pull/699)
- Replace string.split() by string.partition() [#702](https://github.com/plugwise/python-plugwise/pull/702)

## v1.7.0

- Continuous improvements [#678](https://github.com/plugwise/python-plugwise/pull/678)
- Refresh Anna_Elga_2 userdata and adapt, add missing item-count, line-up test-data headers [#679](https://github.com/plugwise/python-plugwise/pull/679)
- Rework code: output a single dict, add gw_data items as Smile-properties [#698](https://github.com/plugwise/python-plugwise/pull/698)

## v1.6.4

- Continuous improvements [#662](https://github.com/plugwise/python-plugwise/pull/662)
- Rework tooling [#664](https://github.com/plugwise/python-plugwise/pull/664)
- Archive p1v4 userdata [#666](https://github.com/plugwise/python-plugwise/pull/666)
- Correct manual_fixtures script [#668](https://github.com/plugwise/python-plugwise/pull/668)
- Improve P1 fault-handling, continuous improvements [#670](https://github.com/plugwise/python-plugwise/pull/670)
- Add control_state to Anna output [#671](https://github.com/plugwise/python-plugwise/pull/671)

## v1.6.3

- Implement cooling-related fixes, trying to solve HA Core issue [#132479](https://github.com/home-assistant/core/issues/132479)

## v1.6.2

- Improve control_state processing:
  - Change value from `off` to `idle` to better match HA Core `HVACAction` states.
  - Handle difference between old and new Adam firmware: set `control_state` based on `setpoint` vs `temperature` for older firmware.
  - Implement fix for [#776](https://github.com/plugwise/plugwise-beta/issues/776), move it from the integration to the backend library.
  - Add a test to cover the code that fixes #776.
  - Update related fixtures and test-data json files.

## v1.6.1

- Support python 3.13

## v1.6.0

- New Feature: implement collection of location/zone data: Plugwise Adam thermostat representations are zone-based instead of device-based.
  Solution for HA Core issue [#130597](https://github.com/home-assistant/core/issues/130597)

## v1.5.2

- Bugfix for Adam: improve recognition of unknown zigbee devices.

## v1.5.1

- Fix typing and rounding of P1 and thermostat sensors, energy-device-related code improvements.
- Rename mode to climate_mode.

## v1.5.0

- Make timeout an internal parameter.

## v1.4.4

- Change connect() function to output the gateway firmware-version.

## v1.4.3

- Clean up timeout-related, pass _request-function as an argument.

## v1.4.2

- Bugfix: implement solution for issue reported in [#739](https://github.com/plugwise/plugwise-beta/issues/739)

## v1.4.1

- Prettying documents with Biome (CLI), fixture layout updated accordingly.

## v1.4.0

- Improve model_id implementation, allow direct access to the gateway `smile_model_id`.

## v1.3.1

- Add missing typing for model_id.

## v1.3.0

- New Feature: add device model_id's to the API output (not for legacy devices).

## v1.2.0

- Improve the low_battery feature, also take the battery-critically-low warning notification into account.

## v1.1.0

- New Feature: add a low_battery binary_sensor for battery-powered devices and block the related battery-low notifications.

## v1.0.0

- First formal release to v1.0.0!

## v0.38.3

- Implement fix for Core Issue [#119686](https://github.com/home-assistant/core/issues/119686)

## v0.38.2

- Lower connection-timeout for actual devices after initial connect

## v0.38.1

- Add missing exception-handling for set-function in `__init__.py`
- Add call_request() functions combining all common exception-handling for all set-functions
- Update and improve test code
- Implementing code improvements as suggested in #567

## v0.38.0

- Add a reboot_gateway() function for actual Plugwise devices.

## v0.37.9

- Correct set_select() function.

## v0.37.8

- Create a set_select() function, combining the set_dhw_mode(), set_gateway_mode(), set_regulation_mode() and set_schedule_state() functions.

## v0.37.7

- Don't output schedule-related data when no valid schedule(s) found.
- Various corrections to impacted test- and data-files/fixtures.

## v0.37.6

- Schedule-related improvements.
- Revert removal of set_temperature_offset() function.

## v0.37.5

- Add setting the thermostat temperature_offset to the set_number() function.
- Fix typo in manual_fixtures.py script.

## v0.37.4 - not released

- Create a set_number() function, combining the set_number_setpoint() and set_temperature_offset() functions.

## v0.37.3

- Fix for [plugwise-beta #620](https://github.com/plugwise/plugwise-beta/issues/620).

## v0.37.2

- Code improvements.
- Remove unused dependencies from pyproject.toml.

## V0.37.1

- Further optimization / deduplication of the refactored code.

## v0.37.0

- Refactor code into separate parts/paths for actual and legacy Plugwise devices.

## v0.36.3

- Bugfixes for [#558](https://github.com/plugwise/plugwise-beta/issues/558) and [#559](https://github.com/plugwise/plugwise-beta/issues/559).

## v0.36.2

- Improve support for Anna+Elga systems that do not support cooling (fix for [#547](https://github.com/plugwise/plugwise-beta/issues/547)).
- Update test-fixtures for Plugwise-beta/Core Plugwise.
- Fix deprecation-warnings.

## v0.36.1

- New Feature: For Adam, implement limited access to the gateway-modes.
- Refresh adam_plus_anna_new userdata and adapt.
- Bump actions and requirements to Python 3.12, where possible.
- Ruff as per #470 (defaulting black and isort to ruff).
- Modularize/split testing, including separation of code and data.
- Improve quality as indicated by SonarCloud.

## v0.36.0 - retracted

## v0.35.4

- Remove support for Adam with fw 2.x and Anna with fw 3.x
- Add 4.4.1 Anna testing (`control_state` added to xml but not active)
- Maintenance, archive older firmware and clean/update tests accordingly
- Introduce quick-fixture generation without testing
- Fix `adam_jip` testcase

## v0.35.3

- Working solution for [Core Issue #104433](https://github.com/home-assistant/core/issues/104433)

## v0.35.2

- Add detection & removal of orphaned heater_central.
- Bugfix for [Core Issue #104433](https://github.com/home-assistant/core/issues/104433)
- Improve/optimize/reorder.
- Typing-constants clean-up.

## v0.35.1

- Update OFF-constant, removal capital begin-letter.

## v0.35.0

- Feature: add "Off" as option in available_schedules, selecting this option will disable the active schedule for a thermostat.
- Fix not being able to turn off a schedule.
- Update fixture to create a testcase for HVACAction.PREHEATING

## v0.34.5

- Adam: return the control_state for each thermostat/location.
- Bugfix: correct removal of obsolete `outdoor_air_temperature` sensor.

## v0.34.4

- Bugfix: avoid device_list growing at every full-update, add device_list to fixtures.

## v0.34.3

- Anna+Elga now always has `cooling_present` set to `True`: the Elga (always) has cooling-capability.
- Cooling-mode on/off is determined from specific Elga status-codes.

## v0.34.2

- Add a list of Plugwise devices to the API.

## v0.34.1 - Skipped

## v0.34.0

- New feature: for Adam, provide mode = off, related to the regulation_mode = off, and mode = cool, for regulation_mode = cooling.
  Also, for Adam, return to providing a single setpoint for both heating and cooling.
- Update userdata, manual-fixture-creation, and tests related to the added modes.
- A few small Typing updates.
- Manually change the adam_jip fixture, for testing in pw-beta/Core plugwise.

## v0.33.2 Bugfix for HA climate

- Remove last_used (schedule) from output.
- Bugfix for [Core Issue #102204](https://github.com/home-assistant/core/issues/102204)
- Add item-count to output.
- Support python 3.12

## v0.33.1 Bugfix for Adam

- Adam: remove use of control_state, xml-key no longer present.
- Fix error in manual fixture creation.

## v0.33.0 Bugfixes, implement daily full-update

- New feature: implement a daily full-update (other part of solution for [HA Core issue #99372](https://github.com/home-assistant/core/issues/99372))
- Reorder device-dicts: gateway first, optionally heater_central second
- Improve handling of obsolete sensors (solution for [HA Core issue #100306](https://github.com/home-assistant/core/issues/100306)
- Improve handling of invalid actuator xml-data (partial solution for [HA Core issue #99372](https://github.com/home-assistant/core/issues/99372)

## v0.32.3 Improve quality by extended testing, bugfix

- Testing: make it possible to emulate binary_sensors, climates, numbers, sensors, switches, etc., updating.
- Add extra updated-testcases for each platform.
- Fix a bug which prevents the updating of the available-state of zigbee devices (correct data-collection at updating).
- Optimize first-time data-collection at initialization.
- Modify the added P1 Plugwise notification so that it does not impact the device-availability.

## v0.32.2 Continuous improvements, bugfix

- Extend p1v4_442_triple userdata to include a Plugwise notification, extending the related fixture which is used in PW-beta and Core Plugwise.
- Optimize and rearrange typing-related constants, implement and cleanup.
- Optimize and reorder code, for the Stretch prevent the creation of a switch-group with an orphaned switch.

## v0.32.1 Improve typing, bugfix

- Integrate the process of creating binary_sensors, sensors, and switches dicts. Should make typing simpler.
- Fix an apparent notification-bug for p1v4.
- Improve typing: fix all type-ignores.
- Clean up no longer used code.
- Remove support for python3.9.

## v0.32.0: New Feature: add support for changing the temperature offset on a supported thermostat device

- Add support for changing the temperature-offset on Jip, Lisa, Tom, Floor and on Anna (in some configurations)
- Fix issue introduced by ruff: replace using .keys() in xml-find result

## v0.31.9: Further typing improvements

- Add NumberType, SelectType and SelectOptionsType constants to improve typing further
- Code quality housekeeping

## v0.31.8: Improve typing as per Core PR #96915

## v0.31.8: Improve typing

- Add BinarySensorType, SensorType, SwitchType as per HA Core PR 96915

## v0.31.7: Various small updates

- Repair coverage/fix testing - #294
- Correct non-unique device names in adam_jip userdata
- Add domestic_hot_water_setpoint data to anna_heatpump_heating userdata, update relevant test-cases
- Add raising an error when providing the wrong type of temperature input to set_temperature() with cooling active
- Add preliminary support for python 3.12 by updating build system requirements
- Code improvements

## v0.31.6: Fix domestic_hot_water_setpoint-related bug for Anna + Elga

- Add guarding for popping domestic_hot_water_setpoint
- Improved fixture generation and prettifying

## v0.31.5: Cooling-related fix/improvements

- Fix cooling-related bug in set_temperature(), raise an error when the user tries to change the not-active setpoint
- Change setpoint_low/_high generation, show the active setpoint and the related min/max values, don't show related setpoints in the active schedule
- Update related test-assert / fixtures
- Improve dhw_setpoint related code

## v0.31.4: Improvements

- Improve fixture generation and manual fixtures, exposing (prettier-ed) fixtures
- Fix unneeded Union-typing

## v0.31.3: Typing updates, improved fixture generation and manual mode-changes

## v0.31.2: Introduce strict-typing (py.typed)

## v0.31.1: Legacy Anna - read and process system-xml data

- Add support for reading the system-xml data from the legacy Smile T
- Repo-generic: CI/CD Improvements

## v0.31.0: Split off the USB-related code: the Plugwise Stick related code has been moved into [#plugwise_usb](https://github.com/plugwise/python-plugwise-usb)

--- Split between Smile/Stretch and USB-Stick related code ---

## v0.27.10: Anna + Elga: final fix for [#320](https://github.com/plugwise/plugwise-beta/issues/320)

## v0.27.9: P1 legacy: collect data from /core/modules

- Collect P1 legacy data from /core/modules - fix for [#368](https://github.com/plugwise/plugwise-beta/issues/368)
- `Dependencies`: Default to python 3.11
- `Development`
  - Improved markdown (i.e. markup and contents), added linter for markdown & added code owners
  - Replaced flake8 linting with ruff (following HA-Core)
  - Improved testing on commit

## v0.27.8: Stick bugfix: fix for reported Plugwise-Beta issue [#347](https://github.com/plugwise/plugwise-beta/issues/347)

- Change message request queue a FiFO queue

## v0.27.7: Stick bugfix: fix for reported issue #312

- [#312](https://github.com/plugwise/plugwise-beta/issues/312)
- Fix Stick-related memory-leaks
- `Dependencies`: Add python 3.11 support

## v0.27.6: Stick bugfix: properly handle responses without mac

## v0.27.5: Bugfix for #340

- [#340](https://github.com/plugwise/plugwise-beta/issues/340)

## v0.27.4: Bugfix for HA Core Issue 85910

- [Core Issue 85910](https://github.com/home-assistant/core/issues/85910)

(# v0.27.3, v0.27.2: were not released)

## v0.27.1: More cooling-related updates, based on additional info from Plugwise

- Updates for Anna+Elga and Adam-OnOff systems
- Loria/Thermastage fix

## v0.27.0: Smile P1: support 3-phase measurements

(# v0.26.0: not released)

## v0.25.14: Improve, bugfix

- Anna+Elga: final solution for [#320](https://github.com/plugwise/plugwise-beta/issues/320)
- Related to [Core Issue 83068](https://github.com/home-assistant/core/issues/83068): handle actuator_functionality or sensor depending on which one is present

## v0.25.13: Anna+Elga, OnOff device: base heating_state, cooling_state on central_heating_state key only

- Partial solution for [#320](https://github.com/plugwise/plugwise-beta/issues/320)
- Improving the solution for [Core Issue 81839](https://github.com/home-assistant/core/issues/81839)

## v0.25.12: Revert remove raising of InvalidSetupError

## v0.25.11: Improve/change contents building on v0.25.10

- Revert: Improve handling of xml-data missing, raise exception with warning; the reason for adding this fix is not clear. Needs further investigation.
- Remove raising of InvalidSetupError, no longer needed; handled in Plugwise config_flow (function added by Frenck)
- Simplify logic calling _power_data_from_location() (similar to v0.21.4); possible solution for [Core Issue 81672](https://github.com/home-assistant/core/issues/81672)
- _full_update_device(): revert back to v0.21.4 logic
- async_update(): not needed to refresh self._modules
- Add fix for Core #81712

## v0.25.10: Thermostats: more improvements

- Anna + Elga: hide cooling_enable switch, (hardware-)switch is on Elga, not in Plugwise App
- Adam: improve collecting regulation_mode-related data. Fix for [#240](https://github.com/plugwise/python-plugwise/issues/240)
- Anna: remove device availability, fix for [Core Issue 81716](https://github.com/home-assistant/core/issues/81716)
- Anna + OnOff device: fix incorrect heating-state, fix for [Core Issue 81839](https://github.com/home-assistant/core/issues/81839)
- Improve handling of xml-data missing, raise exception with warning. Solution for [Core Issue 81672](https://github.com/home-assistant/core/issues/81672)
- Improve handling of empty schedule, fix for [#241](https://github.com/plugwise/python-plugwise/issues/241)

## v0.25.9: Adam: hide cooling-related switch, binary_sensors when there is no cooling present

- This fixes the unexpected appearance of new entities after the Adam 3.7.1 firmware-update
- Properly handle an empty schedule, should fix [#313](https://github.com/plugwise/plugwise-beta/issues/313)

## v0.25.8: Make collection of toggle-data future-proof

## v0.25.7: Correct faulty logic in the v0.25.6 release

## v0.25.6: Revert py.typed, fix Core PR #81531

## v0.25.5: not released

## v0.25.4: Add py.typed, fix typing as suggested in #231

## v0.25.3: Bugfix for #309

- [#309](https://github.com/plugwise/plugwise-beta/issues/309)

## v0.25.2: Bugfix, code improvements

- Fix a set_temperature() and heat_cool related bug

## v0.25.1: Remove sensor-keys from output when cooling is present

## v0.25.0: Improve compatibility with HA Core climate platform

- Change mode cool to heat_cool
- Add setpoint_high/setpoint_low to output

## v0.24.1: Bugfix: fix root-cause of Core issue 79708

- [Core Issue 79708](https://github.com/home-assistant/core/issues/79708)

## v0.24.0: Improve support for Anna-Loria combination

- Replace mode heat_cool by cool (available modes are: auto, heat, cool)
- Add cooling_enabled switch
- Add dhw_mode/dhw_modes (for selector in HA)
- Add dhw_temperature sensor
- Show Plugwise notifications for non-legacy Smile P1

## v0.23.0: Add device availability for non-legacy Smiles

- Add back Adam vacation preset, fixing reopened issue #185

## v0.22.1: Improve solution for issue #213

## v0.22.0: Smile P1 - add a P1 smartmeter device

- Change all gateway model names to Gateway
- Change Anna Smile name to Smile Anna, Anna model name to ThermoTouch
- Change P1 Smile name to Smile P1
- Remove raise error-message, change priority of logger messages to less critical
- Fix for issue #213

## v0.21.3: Revert all hvac_mode HEAT_COOL related

- The Anna-Elga usecase, providing a heating and a cooling setpoint, was reverted back to providing a single setpoint.

## v0.21.2: Code improvements, cleanup

## v0.21.1: Smile: various updates % fixes

- Change Anna-gateway model to Smile - related to [Core blog entity_naming](https://developers.home-assistant.io/blog/2022/07/10/entity_naming/) and changes in the Core Plugwise(-beta) code.
- Output elga_cooling_enabled, lortherm_cooling_enabled or adam_cooling_enabled when applicable. To be used in Core Plugwise(-beta) instead of calling api-variables.
- Protect the self-variables that will no longer be used in Core Plugwise(-beta).
- pyproject.toml updates.
- Adapt test-code where needed.

## v0.21.0: Smile: improve and add to output, fix cooling-bug

- Add `domestic_hot_water_setpoint` to the output. Will become an additional Number in Plugwise(-beta).
- Create separate dicts for `domestic_hot_water_setpoint`, `maximum_boiler_temperature`, and `thermostat` in the output.
- Change `set_max_boiler_temperature()` to `set_number_setpoint()` and make it more general so that more than one Number setpoint can be changed.
- Fix a cooling-related bug (Anna + Elga).
- Improve `set_temperature()`function.
- Update the testcode accordingly.

## v0.20.1: Smile: fix/improve cooling support (Elga/Loria/Thermastage) based on input from Plugwise

## v0.20.0: Adam: add support for the Aqara Plug

## v0.19.1: Smile & Stretch: line up error handling with Plugwise-beta

## v0.19.0: Smile Adam & Anna: cooling-related updates

- Anna: replace `setpoint` with `setpoint_low` and `setpoint_high` when cooling is active
- Anna: update according to recent Anna-with-cooling firmware updates (info provided by Plugwise)
- Anna: handle `cooling_state = on` according to Plugwise specification (`cooling_state = on` and `modulation_level = 100`)
- Move boiler-type detection and cooling-present detection into `_all_device_data()`
- Update/extend testing and corresponding userdata

## v0.18.5: Smile bugfix for #192

- [#192](https://github.com/plugwise/python-plugwise/issues/192)

## v0.18.4: Smile: schedule-related bug-fixes and clean-up

- Update `_last_used_schedule()`: provide the collected schedules as input in order to find the last-modified valid schedule.
- `_rule_ids_by_x()`: replace None by NONE, allowing for simpler typing.
- Remove `schedule_temperature` from output: for Adam the schedule temperature cannot be collected when a schedule is not active.
- Simplify `_schedules()`, don't collect the schedule-details as no longer required.
- Improve solution for plugwise-beta issue #276
- Move HA Core input-checks into the backend library (into set_schedule_state() and set_preset())

## v0.18.3: Smile: move solution for #276 into backend

- [#276](https://github.com/plugwise/plugwise-beta/issues/276)

## v0.18.2: Smile: fix for #187

- [#187](https://github.com/plugwise/plugwise-beta/issues/187)

## v0.18.1: Smile Adam: don't show vacation-preset, as not shown in the Plugwise App or on the local Adam-website

## v0.18.0: Smile: add generation of cooling-schedules

- Further improve typing hints: e.g. all collected measurements are now typed via TypedDicts
- Implement correct generation of schedules for both heating and cooling (needs testing)

## v0.17.8: Smile: Bugfix, improve testing

- Fix [#277](https://github.com/plugwise/plugwise-beta/issues/277)
- Improve incorrect test-case validation

## v0.17.7: Smile: Corrections, fixes, clean up

- Move compressor_state into binary_sensors
- Adam: add missing zigbee_mac to wireless thermostats
- Stretch & Adam: don't show devices without a zigbee_mac, should be orphaned devices
- Harmonize appliance dicts for legacy devices
- Typing improvements
- Fix related test asserts

## v0.17.6: Smile: revert removing LOGGER.error messages

## v0.17.5: Smile: rework to raise instead of return

- raise in error-cases, move LOGGER.debug messages into raise
- clean up code

## v0.17.4 - Smile: improve typing hints, implement mypy testing

## v0.17.3 - Smile Adam: add support for heater_electric type Plugs

## v0.17.2 - Smile Adam: more bugfixes, improvementds

- Bugfix: update set_schedule_state() to handle multi thermostat scenario's
- Improve tracking of the last used schedule, needed due to the changes in set_schedule_state()
- Improve invalid schedule handling
- Update & add related testcases
- Naming cleanup

## v0.17.1 - Smile: bugfix for Core Issue 68621

- [Core Issue 68621](https://github.com/home-assistant/core/issues/68621)

## v0.17.0 - Smile: add more outputs

- Add regulation_mode and regulation_modes to gateway dict, add related set-function
- Add max_boiler_temperature to heater_central dict, add related set-function
- Improve typing hints

## v0.16.9 - Smile: bugfix and improve

- Fix for [#250](https://github.com/plugwise/plugwise-beta/issues/250)
- Rename heatpump outdoor_temperature sensor to outdoor_air_temperature sensor

## v0.16.8 - Smile: bugfixes, continued

- Fix for [Core Issue 68003](https://github.com/home-assistant/core/issues/68003)
- Refix solution for #158

## v0.16.7 - Smile: Bugfixes, more changes and improvements

- Fix for #158: error setting up for systems with an Anna and and Elga (heatpump).
- Block connecting to the Anna when an Adam is present (fixes pw-beta #231).
- Combine helper-functions, possible after removing code related to the device_state sensor.
- Remove single_master_thermostat() function and the related self's, no longer needed.
- Use .get() where possible.
- Implement walrus constructs ( := ) where possible.
- Improve and simplify.

## v0.16.6 - Smile: various changes/improvements

- Provide cooling_state and heating_state as `binary_sensors`, show cooling_state only when cooling is present.
- Clean up gw_data, e.g. remove `single_master_thermostat` key.

## v0.16.5 - Smile: small improvements

- Move schedule debug-message to the correct position.
- Code quality fixes.

## v0.16.4 - Adding measurements

- Expose mac-addresses for network and zigbee devices.
- Expose min/max thermostat (and heater) values and resolution (step in HA).
- Changed mac-addresses in userdata/fixtures to be obfuscated but unique.

## v0.16.3 - Typing

- Code quality improvements.

## v0.16.2 - Generic and Stretch

- As per Core deprecation of python 3.8, removed CI/CD testing and bumped pypi to 3.9 and production.
- Add support for Stretch with fw 2.7.18.

## v0.16.1 - Smile - various updates

- **BREAKING**: Change active device detection, detect both OpenTherm (replace Auxiliary) and OnOff (new) heating and cooling devices.
- Stretch: base detection on the always present Stick
- Add Adam v3.6.x (beta) and Anna firmware 4.2 support (representation and switching on/off of a schedule has changed)
- Anna: Fix cooling_active prediction
- Schedules: always show `available_schemas` and `selected_schema`, also with "None" available and/or selected
- Cleanup and optimize code
- Adapt and improve testcode

## v0.16.0 - Smile - Change output format, allowing full use of Core DataUpdateCoordintor in plugwise-beta

- Change from list- to dict-format for binary_sensors, sensors and switches
- Provide gateway-devices for Legacy Anna and Stretch
- Code-optimizations

## v0.15.7 - Smile - Improve implementation of cooling-function-detection

- Anna: add two sensors related to automatic switching between heating and cooling and add a heating/cooling-mode active indication
- Adam: also provide a heating/cooling-mode active indication
- Fixing #171
- Improved dependency handling (@dependabot)

## v0.15.6 - Smile - Various fixes and improvements

- Adam: collect `control_state` from master thermostats, allows showing the thermostat state as on the Plugwise App
- Adam: collect `allowed_modes` and look for `cooling`, indicating cooling capability being available
- Optimize code: use `_all_appliances()` once instead of 3 times, by updating/changing `single_master_thermostat()`,
- Protect several more variables,
- Change/improve how `illuminance` and `outdoor_temperature` are obtained,
- Use walrus operator where applicable,
- Various small code improvements,
- Add and adapt testcode
- Add testing for python 3.10, improve dependencies (github workflow)
- Bump aiohttp to 3.8.1, remove fixed dependencies

## v0.15.5 - Skipping, not released

## v0.15.4 - Smile - Bugfix: handle removed thermostats

- Recognize when a thermostat has been removed from a zone and don't show it in Core
- Rename Group Switch to Switchgroup, remove vendor name

## v0.15.3 - Skipping, not released

## v0.15.2 - Smile: Implement possible fix for HA Core issue #59711

## v0.15.1 - Smile: Dependency update (aiohttp 3.8.0) and aligning other HA Core dependencies

## v0.15.0 - Smile: remove all HA Core related-information from the provided output

## v0.14.5 - Smile: prepare for using the HA Core DataUpdateCoordintor in Plugwise-beta

- Change the output to enable the use of the HA Core DUC in plugwise-beta.
- Change state_class to "total" for interval- and net_cumulative sensors (following the HA Core sensor platform updates).
- Remove all remnant code related to last_reset (log_date)
- Restructure: introduce additional classes: SmileComm and SmileConnect

## v0.14.2 - Smile: fix P1 legacy location handling error

## v0.14.1 - Smile: removing further `last_reset`s

- As per [Core Blog `state_class_total`](https://developers.home-assistant.io/blog/2021/08/16/state_class_total)

## v0.14.0 - Smile: sensor-platform updates - 2021.9 compatible

## v0.13.1 - Smile: fix point-sensor-names for P1 v2

## v0.13.0 - Smile: fully support P1 legacy (specifically with firmware v2.1.13)

## v0.12.0 - Energy support and bugfixes

- Stick: Add new properties `energy_consumption_today` counter and `energy_consumption_today_last_reset` timestamp. These properties can be used to properly measure the used energy. Very useful for the 'Energy' capabilities introduced in Home Assistant 2021.8
- Stick: Synchronize clock of all plugwise devices once a day
- Stick: Reduced local clock drift from 30 to 5 seconds
- Stick: Optimized retrieval and handling of energy history
- Smile: add the required sensor attributes for Energy support
- Smile: add last_reset timestamps for interval-sensors and cumulative sensors
- Smile: fix the unit_of_measurement of electrical-cumulative-sensors (Wh --> kWh)

## 0.11.2 - Fix new and remaining pylint warnings

## 0.11.1 - Code improvements

- Smile: improve use of protection for functions and parameter
- Fix pylint warnings and errors

## 0.11.0 - Smile: add support for the Plugwise Jip

- Adam, Anna: don't show removed thermostats / thermostats without a location

## 0.10.0 - Smile: move functionality into backend, rearrange data in output

- Rearrange data: the outputs of get_all_devices() and get_device_data() are combined into self.gw_devices. Binary_sensors, sensors and switches are included with all their attributes, in lists.
- Two classes have been added (entities.py), one for master_thermostats and one for binary_sensors, these classes now handle the processing of data previously done in plugwise-beta (climate.py and binary_sensor.py).

## 0.9.4 - Bugfix and improvements

- Stick: make stick code run at python 3.9 (fixes AttributeError: 'Thread' object has no attribute 'isAlive')
- Smile: underlying code improvements (solve complexity, linting, etc.), continuing to improve on the changes implemented in v0.9.2.

## 0.9.3 - Smile: add lock-state switches

- Add support for getting and setting the lock-state of Plugs-, Circles-, Stealth-switches, for Adam and Stretch only. A set lock-state prevents a switch from being turned off.
- There is no lock_state available for the following special Plugwise classes: `central heating pump` and `value actuator`

## 0.9.2 - Smile: optimize

- Functions not called by the plugwise(-beta) code have been moved to helper.py in which they are part of the subclass SmileHelper
- All for-loops are now executed only once, the results are stored in self-parameters.
- Added fw, model and vendor information into the output of get_device_data(), for future use in the HA Core Plugwise(-beta) Integration
- Split off HEATER_CENTRAL_MEASUREMENTS from DEVICE_MEASUREMENTS so they can be blocked when there is no Auxiliary device present
- Collect only the data from the Smile that is needed: full_update_device() for initialisation, update-device() for updating of live data
- Adapt test_smile.py to the new code, increase test-coverage further

## 0.9.1 - Smile: add Domestic Hot Water Comfort Mode switch - Feature request

## 0.9.0 - Stick: API change

- Improvement: Debounce relay state
- Improvement: Prioritize request so requests like switching a relay get send out before power measurement requests.
- Improvement: Dynamically change the refresh interval based on the actual discovered nodes with power measurement capabilities
- Added: New property attributes for USB-stick.
  The old methods are still available but will give a deprecate warning
  - Stick
    - `devices` (dict) - All discovered and supported plugwise devices with the MAC address as their key
    - `joined_nodes` (integer) - Total number of registered nodes at Plugwise Circle+
    - `mac` (string) - The MAC address of the USB-Stick
    - `network_state` (boolean) - The state (on-line/off-line) of the Plugwise network.
    - `network_id` (integer) - The ID of the Plugwise network.
    - `port` (string) - The port connection string
  - All plugwise devices
    - `available` (boolean) - The current network availability state of the device
    - `battery_powered` (boolean) - Indicates if device is battery powered
    - `features` (tuple) - List of supported attribute IDs
    - `firmware_version` (string) - Firmware version device is running
    - `hardware_model` (string) - Hardware model name
    - `hardware_version` (string) - Hardware version of device
    - `last_update` (datetime) - Date/time stamp of last received update from device
    - `mac` (string) - MAC address of device
    - `measures_power` (boolean) - Indicates if device supports power measurement
    - `name` (string) - Name of device based om hardware model and MAC address
    - `ping` (integer) - Network roundtrip time in milliseconds
    - `rssi_in` (integer) - Inbound RSSI level in DBm
    - `rssi_out` (integer) - Outbound RSSI level based on the received inbound RSSI level of the neighbor node in DBm
  - Scan devices
    - `motion` (boolean) - Current detection state of motion.
  - Sense devices
    - `humidity` (integer) - Last reported humidity value.
    - `temperature` (integer) - Last reported temperature value.
  - Circle/Circle+/Stealth devices
    - `current_power_usage` (float) - Current power usage (Watts) during the last second
    - `current_power_usage_8_sec` (float) - Current power usage (Watts) during the last 8 seconds
    - `power_consumption_current_hour` (float) - Total power consumption (kWh) this running hour
    - `power_consumption_previous_hour` (float) - Total power consumption (kWh) during the previous hour
    - `power_consumption_today` (float) - Total power consumption (kWh) of today
    - `power_consumption_yesterday` (float) - Total power consumption (kWh) during yesterday
    - `power_production_current_hour` (float) - Total power production (kWh) this hour
    - `relay_state` (boolean) - State of the output power relay. Setting this property will operate the relay
  - Switch devices
    - `switch` (boolean) - Last reported state of switch
  - Stretch v2: fix failed connection by re-adding the aiohttp-workaround

## 0.8.6 - Stick: code quality improvements

- Bug-fix: Power history was not reported (0 value) during last week of the month
- Improvement: Validate message checksums
- Improvement: Do a single ping request to validate if node is on-line
- Improvement: Guard Scan sensitivity setting to medium
- Improvement: Move general module code of messages, nodes, connection to the **init**.py files.
- Improvement: Do proper timeout handling while sequence counter resets (once every 65532 messages)
- Improvement: Better code separation. All logic is in their designated files:
  1. Connection (connection/\*.py)
  2. Data parsing (parser.py)
  3. Data encoding/decoding of message (messages/\*.py)
  4. Message handling - Initialization & transportation (controller.py)
  5. Message processing - Do the required stuff (stick.py & nodes/\*.py)
- Improvement: Resolves all flake8 comments

## 0.8.5 - Smile: fix sensor scaling

- Fix for HA Core issue #44349
- Fix other value scaling bugs
- Remove aiohttp-workaround - issue solved in aiohttp 3.7.1

(## 0.8.4 - Not released: Fix "Gas Consumed Interval stays 0" )

## 0.8.2/0.8.3 - Smile: code quality improvements

- Switch Smile to defusedxml from lxml (improving security)
- Lint and flake recommendations fixed
- Project CI changes
- Bug-fix: fix use of major due to change of using semver.VersionInfo.
- Add model-info: to be used in Core to provide a more correct model-name for each device.
- Code improvements and increase in test-coverage.

## 0.8.1 - Stick: standardize logging

## 0.8.0 - Merged Smile/Stick module

- Merge of the former network and former USB module to a single python module
- Improved commit/test/CI&CD
- Notifications handling for fixtures

---

Changelogs below this line are separated in the former python-plugwise USB-only fork from @brefra and the former Plugwise_Smile Network-only module by @bouwew and @CoMPaTech

---

## Old change log python-plugwise

### 2.0.2 - Get MAC-address of stick

### 2.0.1 - Fixes and optimizations

### 2.0.0 - Support for Scan devices, (un)join of new devices and experimental support for Sense

- [All details](https://github.com/brefra/python-plugwise/releases/tag/2.0.0) in the release tag

### 1.2.2 - Logging level corrections

### 1.2.1 - Watchdog exception fix

### 1.2.0 - Fixes and changes

- Return power usage even if it's 0
- Callbacks for nodes discovered after initial scan

### 1.1.1 - Rewritten connection logic

- Registered node counter
- Improved reliability of node discovery
- Fixed negative power usage

### alpha - rewrite to async

## Change log former Smile

### 1.6.0 - Adam: improved support for city-heating

### 1.5.1 - Decrease sensitivity for future updates

### 1.5.0 - Add delete_notification service

- Add a service to dismiss/delete the Plugwise Notification(s) from within HA Core (plugwise.delete_notification)
- Improve detection of switch-groups and add group switching for the Stretch

### 1.4.0 - Stretch and switch-groups

- Improve error handling, add group switching of plugs (Adam).

### 1.3.0 - Only released in alpha/beta

- Initial support for Stretch (v2/v3) including tests
- Force gzip encoding, work-around for aiohttp-error
- Improve P1 DSMR legacy support
- Ensure `gateway_id` is properly defined (i.e. not `None`)
- b4: Use `domain_objects` over `direct_objects` endpoints
- Remove py3x internal modules (as requested per #86)
- CI-handling improvements and both 3.7 and 3.8 testing
- Code cleanup and output formatting improvements

### 1.2.2 - Re-fix notifications

### 1.2.1 - Fix url display, cleanup and adding tests

### 1.2.0 - HA-Core config_flow unique_id fixes

- Fix situation where `unique_id` was set to `None` for legacy P1 DSMRs
- Introduce using the (discovered) hostname as unique_id

### 1.1.2 - Fix notifications-related bugs

### 1.1.0 - Add HA-core test-fixtures, Plugwise notifications and improvement of error-detection

- Add exporter for fixtures to be used by HA-core for testing plugwise
- Improve `error`-detection
- Expose Plugwise System notifications (i.e. warnings or errors visible in the app)

### 1.0.0 - Stable release

- Just blacked code (Python `black`)

### 0.2.15 - Code cleanup

- Just code improvements

### 0.2.14 - Code cleanup

- Just code improvements

### 0.2.13 - Final legacy fix

- Adjust `dwh` and `setpoint` handling

### 0.2.12 - Fix available schema's

- Thanks to report from @fsaris
- Adept code to allow for change introduced by firmware 4.x

### 0.2.11 - Add community requested sensors

- See [65](https://github.com/plugwise/plugwise-beta/issues/65)
- Add return water temperature from Auxiliary

### 0.2.10 - Core PR updates

- Add exception for InvalidAuthentication
- Revert setting heating when None

### 0.2.9 - Use intended state

- Change to `intended_central_heating_state`

### 0.2.8 - Asynchronous HTTP improvement, firmware 4.x testing

- Code improvement for asyncio
- Added firmware 4.x test data and tests
- CI/CD improve pre-commit hooks
- Remove useless water sensor
- Improve testing guidelines README

### 0.2.7 - CI/CD

- CI/CD Version number handling

### 0.2.6 - New firmware support and XML handling

- Improvement by contributor @sbeukers (Smile P1 v4 support)
- Legacy Anna fixes and test improvements
- Favour `domain_objects` over `appliances` XML-data

### 0.2.5 - Issuefix, cleanup and CI/CD

- Fix for HVAC idle issue [#57](https://github.com/plugwise/plugwise-beta/issues/57)
- Improve XML
- Remove debug output
- CI/CD handling

### 0.2.4 Legacy Anna fixes and Auxiliary handling

- `chs` and `dhw` determined from `boiler_state`
- No `chs` or `dhw` on legacy Anna
- More legacy anna fixes

### 0.2.1 - Master thermostat fixes

- Legacy Anna fixes
- Auxiliary tests
- Fix for `smt` (single master thermostat)
- CI/CD Improved testing
- Sensor value rounding

### 0.2.0 - Second beta release

- Improve sensor names
- Handle `set`-commands in testing
- Code style improvements (lint/black)

### 0.1.26 - Documentation and CI/CD improvements

- Create further testing
- Improve coverage/linting/etc.
- Prepare virtualenvs (travis etc.)
- Code styling/wording fixes (lint/pep)
- Improve READMEs

### 0.1.25 - Domestic hot water and CI/CD improvements

- Testing improvements
- `dhw`-handling

### 0.1.24 - Add handling erroneous XML and/or timeouts

- Favour exception raises above returning `False`
- Restructure full device update accordingly
- Add Plugwise Exceptions
- CI/CD add tests accordingly

### 0.1.23 - Code quality improvements

- FutureWarnings acted accordingly

### 0.1.22 - Add scheduled temperature in output

### 0.1.21 - CI/CD improvements

- Add heatpump-environment data and tests (thanks to @marcelveldt)
- Improve `outdoor_temperature` accordingly (favour Auxiliary over Smile)

### 0.1.20 - Fix thermostat count

### 0.1.19 - Add thermostat counting

### 0.1.18 - Add flame state

### 0.1.17 - Code improvements

- Squash device names

### 0.1.16 - Fix central components

- Version skip to align with `-beta`-component

### 0.1.12 - Introduce heatpump

- Thanks to @marcelveldt and his environment
- Coherent heating/cooling state

### 0.1.11 - Add all options for P1 DSMR

- Thanks to @(tbd) and his environment

### 0.1.9 - Set HVAC on legacy Anna

### 0.1.8 - Scheduled state on legacy Anna

### 0.1.7 - Legacy Anna small improvements

### 0.1.6 - Fix schedules for Legacy Anna's

### 0.1.2 - Code improvements and public variables

- More linting
- Cleanup scan_thermostat
- Cleanup unused variables
- Improve/standardize public variables
- Tests updated accordingly
- Version skip to align with `-beta`-component

### 0.1.0 - Public beta

### 0.0.57 - Review to public beta

- Delete fugly sleeping
- Improve binary sensors
- Update tests accordingly

### 0.0.56 - Documentation and code improvements

- `black`
- READMEs updated

### 0.0.55 - `dhw` off for legacy Anna

### 0.0.54 - Gateway detection (which smile)

### 0.0.53 - Gateway detection (which smile)

### 0.0.52 - Fix for Legacy anna missing devices

### 0.0.51 - Add Anna firmware 4.x support

### 0.0.43 - Thermostat finding and peak/net P1 DSMR values

- Fix peak values for DSMR
- Calculate net (netto) values
- Thermostat finder
- Add tests accordingly

### 0.0.40 - Legacy Anna and legacy P1 introduction

- Re-introduce legacy Anna from `haanna`/`anna-ha`
- Add legacy P1 DSMR
- Including tests

### 0.0.27 - Prepare for HA config flow and multiple devices

- Add tests and location mapping
- Improve handling Lisa thermostat
- Improve relay (plugs) functionality
- Add individual Smiles as 'hub'-components

### 0.0.26 - Add relay (plugs) support and tests

### 0.0.x - Not individually release but left in old repository

- [this repo](https://github.com/plugwise/Plugwise-HA)

### x.x.x - Before that commits where made in haanna

- [haanna](https://github.com/laetificat/haanna)
- After mostly leaving `haanna` as a stale project (where @bouwew didn't have PyPi permissions) development was shortly split between personal repositories from both @bouwew and @CoMPaTech before we decided to fully rewrite - from scratch - it to `Plugwise-HA` which was renamed to `Plugwise_Smile` from 0.0.26 onwards.
