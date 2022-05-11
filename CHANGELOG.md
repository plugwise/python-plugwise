# Changelog

# v0.18.2: Smile: fix for https://github.com/home-assistant/core/pull/71642 = https://github.com/plugwise/python-plugwise/issues/187

# v0.18.1: Smile Adam: don't show vacation-preset, as not shown in the Plugwise App or on the local Adam-website

# v0.18.0: Smile: add generation of cooling-schedules
- Further improve typing hints: e.g. all collected measurements are now typed via TypedDicts
- Implement correct generation of schedules for both heating and cooling (needs testing)

# v0.17.8: Smile: Bugfix, improve testing
- Fix https://github.com/plugwise/plugwise-beta/issues/277
- Improve incorrect test-case validation

# v0.17.7: Smile: Corrections, fixes, clean up
- Move compressor_state into binary_sensors
- Adam: add missing zigbee_mac to wireless thermostats
- Stretch & Adam: don't show devices without a zigbee_mac, should be orphaned devices
- Harmonize appliance dicts for legacy devices
- Typing improvements
- Fix related test asserts

# v0.17.6: Smile: revert removing LOGGER.error messages

# v0.17.5: Smile: rework to raise instead of return
- raise in error-cases, move LOGGER.debug messages into raise
- clean up code

# v0.17.4 - Smile: improve typing hints, implement mypy testing

# v0.17.3 - Smile Adam: add support for heater_electric type Plugs

# v0.17.2 - Smile Adam: more bugfixes, improvementds
- Bugfix: update set_schedule_state() to handle multi thermostat scenario's
- Improve tracking of the last used schedule, needed due to the changes in set_schedule_state()
- Improve invalid schedule handling
- Update & add related testcases
- Naming cleanup

# v0.17.1 - Smile: bugfix for https://github.com/home-assistant/core/issues/68621

# v0.17.0 - Smile: add more outputs
- Add regulation_mode and regulation_modes to gateway dict, add related set-function
- Add max_boiler_temperature to heater_central dict, add related set-function
- Improve typing hints

# v0.16.9 - Smile: bugfix and improve
- Fix for https://github.com/plugwise/plugwise-beta/issues/250
- Rename heatpump outdoor_temperature sensor to outdoor_air_temperature sensor

# v0.16.8 - Smile: bugfixes, continued
- Fix for https://github.com/home-assistant/core/issues/68003
- Refix solution for #158 

# v0.16.7 - Smile: Bugfixes, more changes and improvements
- Fix for #158: error setting up for systems with an Anna and and Elga (heatpump).
- Block connecting to the Anna when an Adam is present (fixes pw-beta #231).
- Combine helper-functions, possible after removing code related to the device_state sensor.
- Remove single_master_thermostat() function and the related self's, no longer needed.
- Use .get() where possible.
- Implement walrus constructs ( := ) where possible.
- Improve and simplify.

# v0.16.6 - Smile: various changes/improvements
- Provide cooling_state and heating_state as `binary_sensors`, show cooling_state only when cooling is present.
- Clean up gw_data, e.g. remove `single_master_thermostat` key.

# v0.16.5 - Smile: small improvements
- Move schedule debug-message to the correct position.
- Code quality fixes.

# v0.16.4 - Adding measurements
- Expose mac-addresses for network and zigbee devices.
- Expose min/max thermostat (and heater) values and resolution (step in HA).
- Changed mac-addresses in userdata/fixtures to be obfuscated but unique. 

# v0.16.3 - Typing
- Code quality improvements.

# v0.16.2 - Generic and Stretch
- As per Core deprecation of python 3.8, removed CI/CD testing and bumped pypi to 3.9 and production.
- Add support for Stretch with fw 2.7.18.

# v0.16.1 - Smile - various updates:
- BREAKING: Change active device detection, detect both OpenTherm (replace Auxiliary) and OnOff (new) heating and cooling devices.
- Stretch: base detection on the always present Stick
- Add Adam v3.6.x (beta) and Anna firmware 4.2 support (representation and switching on/off of a schedule has changed)
- Anna: Fix cooling_active prediction
- Schedules: always show `available_schemas` and `selected_schema`, also with "None" available and/or selected
- Cleanup and optimize code
- Adapt and improve testcode

# v0.16.0 - Smile - Change output format, allowing full use of Core DataUpdateCoordintor in plugwise-beta
- Change from list- to dict-format for binary_sensors, sensors and switches
- Provide gateway-devices for Legacy Anna and Stretch
- Code-optimizations

# v0.15.7 - Smile - Improve implementation of cooling-function-detection
- Anna: add two sensors related to automatic switching between heating and cooling and add a heating/cooling-mode active indication
- Adam: also provide a heating/cooling-mode active indication
- Fixing #171
- Improved dependency handling (@dependabot)

# v0.15.6 - Smile - Various fixes and improvements
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

# v0.15.5 - Skipping, not released

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

- As per https://developers.home-assistant.io/blog/2021/08/16/state_class_total

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

- Just `black`ened code (Python `black`)

### 0.2.15 - Code cleanup

- Just code improvements

### 0.2.14 - Code cleanup

- Just code improvements

### 0.2.13 - Final legacy fix

- Adjust `dwh` and `setpoint` handling

### 0.2.12 - Fix available schema's

- Thanks to report from @fsaris
- Adept code to allow for change introducted by firmware 4.x

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

### 0.0.x - Not individually release but left in [this repo](https://github.com/plugwise/Plugwise-HA)

### x.x.x - Before that commits where made in [haanna](https://github.com/laetificat/haanna)

- After mostly leaving `haanna` as a stale project (where @bouwew didn't have PyPi permissions) development was shortly split between personal repositories from both @bouwew and @CoMPaTech before we decided to fully rewrite - from scratch - it to `Plugwise-HA` which was renamed to `Plugwise_Smile` from 0.0.26 onwards.
