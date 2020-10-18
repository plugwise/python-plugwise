# Changelog

## 0.8.0 - Merged Smile/USB module
  - Merge of the former network and former USB module to a single python module
  - Improved commit/test/CI&CD
  - Notifications handling for fixtures

---

Changelogs below this line are separated in the former python-plugwise USB-only fork from @brefra and the former Plugwise_Smile Network-only module by @bouwew and @CoMPaTech

---

## 2.0.2 - Get MAC-address of stick

## 2.0.1 - Fixes and optimizations

## 2.0.0 - Support for Scan devices, (un)join of new devices and experimental support for Sense
  - [All details](https://github.com/brefra/python-plugwise/releases/tag/2.0.0) in the release tag

## 1.2.2 - Logging level corrections

## 1.2.1 - Watchdog exception fix

## 1.2.0 - Fixes and changes
  - Return power usage even if it's 0
  - Callbacks for nodes discovered after initial scan

## 1.1.1 - Rewritten connection logic
  - Registered node counter
  - Improved reliability of node discovery
  - Fixed negative power usage

## alpha - rewrite to async

---

## formerSmile#1.6.0 - Adam: improved support for city-heating

## formerSmile#1.5.1 - Decrease sensitivity for future updates

## formerSmile#1.5.0 - Add delete_notification service
  - Add a service to dismiss/delete the Plugwise Notification(s) from within HA Core (plugwise.delete_notification)
  - Improve detection of switch-groups and add group switching for the Stretch

## formerSmile#1.4.0 - Stretch and switch-groups
  - Improve error handling, add group switching of plugs (Adam).

## formerSmile#1.3.0 - Only released in alpha/beta
  - Initial support for Stretch (v2/v3) including tests
  - Force gzip encoding, work-around for aiohttp-error
  - Improve P1 DSMR legacy support
  - Ensure `gateway_id` is properly defined (i.e. not `None`)
  - b4: Use `domain_objects` over `direct_objects` endpoints
  - Remove py3x internal modules (as requested per #86)
  - CI-handling improvements and both 3.7 and 3.8 testing
  - Code cleanup and output formatting improvements

## formerSmile#1.2.2 - Re-fix notifications

## formerSmile#1.2.1 - Fix url display, cleanup and adding tests

## formerSmile#1.2.0 - HA-Core config_flow unique_id fixes
  - Fix situation where `unique_id` was set to `None` for legacy P1 DSMRs
  - Introduce using the (discovered) hostname as unique_id

## formerSmile#1.1.2 - Fix notifications-related bugs

## formerSmile#1.1.0 - Add HA-core test-fixtures, Plugwise notifications and improvement of error-detection
  - Add exporter for fixtures to be used by HA-core for testing plugwise
  - Improve `error`-detection
  - Expose Plugwise System notifications (i.e. warnings or errors visible in the app)
  
## formerSmile#1.0.0 - Stable release
  - Just `black`ened code (Python `black`)

## formerSmile#0.2.15 - Code cleanup
  - Just code improvements
  
## formerSmile#0.2.14 - Code cleanup
  - Just code improvements
  
## formerSmile#0.2.13 - Final legacy fix
  - Adjust `dwh` and `setpoint` handling
  
## formerSmile#0.2.12 - Fix available schema's
  - Thanks to report from @fsaris
  - Adept code to allow for change introducted by firmware 4.x
    
## formerSmile#0.2.11 - Add community requested sensors
  - See [65](https://github.com/plugwise/plugwise-beta/issues/65)
  - Add return water temperature from Auxiliary
  
## formerSmile#0.2.10 - Core PR updates
  - Add exception for InvalidAuthentication
  - Revert setting heating when None 
  
## formerSmile#0.2.9 - Use intended state
  - Change to `intended_central_heating_state`

## formerSmile#0.2.8 - Asynchronous HTTP improvement, firmware 4.x testing
  - Code improvement for asyncio
  - Added firmware 4.x test data and tests
  - CI/CD improve pre-commit hooks
  - Remove useless water sensor
  - Improve testing guidelines README
  
## formerSmile#0.2.7 - CI/CD
  - CI/CD Version number handling
  
## formerSmile#0.2.6 - New firmware support and XML handling
  - Improvement by contributor @sbeukers (Smile P1 v4 support)
  - Legacy Anna fixes and test improvements
  - Favour `domain_objects` over `appliances` XML-data
  
## formerSmile#0.2.5 - Issuefix, cleanup and CI/CD
  - Fix for HVAC idle issue [#57](https://github.com/plugwise/plugwise-beta/issues/57)
  - Improve XML
  - Remove debug output
  - CI/CD handling

## formerSmile#0.2.4 Legacy Anna fixes and Auxiliary handling
  - `chs` and `dhw` determined from `boiler_state`
  - No `chs` or `dhw` on legacy Anna
  - More legacy anna fixes
  
## formerSmile#0.2.1 - Master thermostat fixes
  - Legacy Anna fixes
  - Auxiliary tests
  - Fix for `smt` (single master thermostat)
  - CI/CD Improved testing
  - Sensor value rounding

## formerSmile#0.2.0 - Second beta release
  - Improve sensor names
  - Handle `set`-commands in testing
  - Code style improvements (lint/black)

## formerSmile#0.1.26 - Documentation and CI/CD improvements
  - Create further testing
  - Improve coverage/linting/etc.
  - Prepare virtualenvs (travis etc.)
  - Code styling/wording fixes (lint/pep)
  - Improve READMEs
  
## formerSmile#0.1.25 - Domestic hot water and CI/CD improvements
  - Testing improvements
  - `dhw`-handling
  
## formerSmile#0.1.24 - Add handling erronous XML and/or timeouts
  - Favour exception raises above returning `False`
  - Restructure full device update accordingly
  - Add Plugwise Exceptions
  - CI/CD add tests accordingly

## formerSmile#0.1.23 - Code quality improvements
  - FutureWarnings acted accordingly

## formerSmile#0.1.22 - Add scheduled temperature in output

## formerSmile#0.1.21 - CI/CD improvements
  - Add heatpump-environment data and tests (thanks to @marcelveldt)
  - Improve `outdoor_temperature` accordingly (favour Auxiliary over Smile)
  
## formerSmile#0.1.20 - Fix thermostat count

## formerSmile#0.1.19 - Add thermostat counting

## formerSmile#0.1.18 - Add flame state

## formerSmile#0.1.17 - Code improvements
  - Squash device names

## formerSmile#0.1.16 - Fix central components
  - Version skip to align with `-beta`-component
  
## formerSmile#0.1.12 - Introduce heatpump
  - Thanks to @marcelveldt and his environment
  - Coherent heating/cooling state
  
## formerSmile#0.1.11 - Add all options for P1 DSMR
  - Thanks to @(tbd) and his environment
  
## formerSmile#0.1.9 - Set HVAC on legacy Anna

## formerSmile#0.1.8 - Scheduled state on legacy Anna

## formerSmile#0.1.7 - Legacy Anna small improvements

## formerSmile#0.1.6 - Fix schedules for Legacy Anna's

## formerSmile#0.1.2 - Code improvements and public variables
  - More linting
  - Cleanup scan_thermostat
  - Cleanup unused variables
  - Improve/standardize public variables
  - Tests updated accordingly
  - Version skip to align with `-beta`-component
  
## formerSmile#0.1.0 - Public beta

## formerSmile#0.0.57 - Review to public beta
  - Delete fugly sleeping
  - Improve binary sensors
  - Update tests accordingly

## formerSmile#0.0.56 - Documentation and code improvements
  - `black`
  - READMEs updated

## formerSmile#0.0.55 - `dhw` off for legacy Anna

## formerSmile#0.0.54 - Gateway detection (which smile)

## formerSmile#0.0.53 - Gateway detection (which smile)

## formerSmile#0.0.52 - Fix for Legacy anna missing devices

## formerSmile#0.0.51 - Add Anna firmware 4.x support

## formerSmile#0.0.43 - Thermostat finding and peak/net P1 DSMR values
  - Fix peak values for DSMR
  - Calculate net (netto) values
  - Thermostat finder
  - Add tests accordingly

## formerSmile#0.0.40 - Legacy Anna and legacy P1 introduction
  - Re-introduce legacy Anna from `haanna`/`anna-ha`
  - Add legacy P1 DSMR
  - Including tests

## formerSmile#0.0.27 - Prepare for HA config flow and multiple devices
  - Add tests and location mapping
  - Improve handling Lisa thermostat
  - Improve relay (plugs) functionality
  - Add individual Smiles as 'hub'-components
  
## formerSmile#0.0.26 - Add relay (plugs) support and tests

## formerSmile#0.0.x - Not individually release but left in [this repo](https://github.com/plugwise/Plugwise-HA)

## formerSmile#x.x.x - Before that commits where made in [haanna](https://github.com/laetificat/haanna)
  - After mostly leaving `haanna` as a stale project (where @bouwew didn't have PyPi permissions) development was shortly split between personal repositories from both @bouwew and @CoMPaTech before we decided to fully rewrite - from scratch - it to `Plugwise-HA` which was renamed to `Plugwise_Smile` from 0.0.26 onwards.
