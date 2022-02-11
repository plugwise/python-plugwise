# Short todo

TODO: delete before merge :)

- [ ] Fetch hardwarwe version (str|None)
  - [ ] inside objects as `<module id=` -> `<hardware_version`
- [ ] Look into binary sensor for firmware update 
- [ ] Add mac addresses (str|none) where applicable
  - [x] Gateways
  - [x] Plugs
  - `Added preliminary tests on legacy anna, anna fw42, and adam_multiple_devices_per_zone`
  - [ ] Decide on more testing
- [ ] from actuator functionality (xml) import
  - [x] inside objects as `<actuator_functionalities>` -> `<thermostat_functionality id=` -> below entries
  - [x] <lower_bound>4</lower_bound>
  - [x] <upper_bound>30</upper_bound>
  - [x] <resolution>0.1</resolution> (step in HA)
  - `Added preliminary tests on legacy anna and anna fw42`
  - [ ] Decide on more testing
