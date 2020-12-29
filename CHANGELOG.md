# Changelog

## 0.8.7 - API change for stick

- Improvement: Debounce relay state
- Added: New property attributes for USB-stick.
  The old functions are still available but will give a deprecate warning
  - Stick
    - `discovered_nodes` (list) - List of MAC addresses of all discovered nodes
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
    - `rssi_in` (DBm) - Inbound RSSI level
    - `rssi_out` (DBm) - Outbound RSSI level based on the received inbound RSSI level of the neighbor node
  - Scan devices
    - `motion` (boolean) - Current detection state of motion.
  - Sense devices
    - `humidity`  (integer) - Last reported humidity value.
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
    - `switch`  (boolean) - Last reported state of switch

## 0.8.6 - Code quality improvements for stick

- Bug-fix: Power history was not reported (0 value) during last week of the month
- Improvement: Validate message checksums
- Improvement: Do a single ping request to validate if node is on-line
- Improvement: Guard Scan sensitivity setting to medium
- Improvement: Move general module code of messages, nodes, connection to the  __init__.py files.
- Improvement: Do proper timeout handling while sequence counter resets (once every 65532 messages)
- Improvement: Better code separation. All logic is in their designated files:
  1. Connection (connection/*.py)
  2. Data parsing (parser.py)
  3. Data encoding/decoding of message (messages/*.py)
  4. Message handling - Initialization & transportation (controller.py)
  5. Message processing - Do the required stuff (stick.py & nodes/*.py)
- Improvement: Resolves all flake8 comments

## 0.8.5 - Fix sensor scaling
  - Fix for via HA Core issue #44349
  - Fix other value scaling bugs
  - Remove aiohttp-workaround - issue solved in aiohttp 3.7.1

(## 0.8.4 - Not released: Fix "Gas Consumed Interval stays 0" )

## 0.8.2/0.8.3 - Code quality improvements

- Switch Smile to defusedxml from lxml (improving security)
- Lint and flake recommendations fixed
- Project CI changes
- Bug-fix: fix use of major due to change of using semver.VersionInfo.
- Add model-info: to be used in Core to provide a more correct model-name for each device.
- Code improvements and increase in test-coverage.

## 0.8.1 - Standardize logging for stick

## 0.8.0 - Merged Smile/USB module

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
