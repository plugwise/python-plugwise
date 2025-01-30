#!/usr/bin/env python3
"""Generate manual fixtures from existing fixtures."""

import json
import os


def json_writer(manual_name: str, output: dict) -> None:
    """Standardized writing json files."""
    if not os.path.exists(f"./fixtures/{manual_name}"):
        os.makedirs(f"./fixtures/{manual_name}")

    outfile = f"./fixtures/{manual_name}/data.json"
    data = json.dumps(
        output,
        indent=2,
        separators=(",", ": "),
        sort_keys=True,
        default=lambda x: list(x) if isinstance(x, set) else x,
    )
    with open(outfile, "w") as f:
        f.write(data + "\n")


print("... Crafting m_* fixtures from userdata ...")  # noqa: T201


# Modified Adam fixtures

base_adam_manual = "adam_multiple_devices_per_zone"
basefile = f"./fixtures/{base_adam_manual}/data.json"

io = open(basefile)
base = json.load(io)

adam_multiple_devices_per_zone = base.copy()

# Change schedule to not present for "446ac08dd04d4eff8ac57489757b7314"
adam_multiple_devices_per_zone["446ac08dd04d4eff8ac57489757b7314"].pop("available_schedules")
adam_multiple_devices_per_zone["446ac08dd04d4eff8ac57489757b7314"].pop("select_schedule")

json_writer("m_adam_multiple_devices_per_zone", adam_multiple_devices_per_zone)

base_adam_manual = "adam_jip"
basefile = f"./fixtures/{base_adam_manual}/data.json"

io = open(basefile)
base = json.load(io)

adam_jip = base.copy()

# Change mode to off for "06aecb3d00354375924f50c47af36bd2" for testcoverage in HA Core
adam_jip["06aecb3d00354375924f50c47af36bd2"]["climate_mode"] = "off"
# Remove control_state for testcoverage of missing control_state in HA Core
adam_jip["06aecb3d00354375924f50c47af36bd2"].pop("control_state")

json_writer("m_adam_jip", adam_jip)


### Manual Adam fixtures

base_adam_manual = "adam_plus_anna_new"
basefile = f"./fixtures/{base_adam_manual}/data.json"

io = open(basefile)
base = json.load(io)

m_adam_cooling = base.copy()

# Remove devices 67d73d0bd469422db25a618a5fb8eeb0, 29542b2b6a6a4169acecc15c72a599b8 and 10016900610d4c7481df78c89606ef22 from anywhere
m_adam_cooling.pop("29542b2b6a6a4169acecc15c72a599b8")
m_adam_cooling.pop("67d73d0bd469422db25a618a5fb8eeb0")
m_adam_cooling.pop("10016900610d4c7481df78c89606ef22")

# Correct setpoint for device "ad4838d7d35c4d6ea796ee12ae5aedf8" and zone "f2bf9048bef64cc5b6d5110154e33c81"
m_adam_cooling["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "setpoint"
] = 23.5
m_adam_cooling["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "temperature"
] = 25.8
m_adam_cooling["f2bf9048bef64cc5b6d5110154e33c81"]["thermostat"][
    "setpoint"
] = 23.5
m_adam_cooling["f2bf9048bef64cc5b6d5110154e33c81"]["sensors"][
    "temperature"
] = 25.8
m_adam_cooling["f2bf9048bef64cc5b6d5110154e33c81"][
    "select_schedule"
] = "off"
m_adam_cooling["f2bf9048bef64cc5b6d5110154e33c81"][
    "control_state"
] = "cooling"
m_adam_cooling["f2bf9048bef64cc5b6d5110154e33c81"]["climate_mode"] = "cool"

# Add new key available
m_adam_cooling["ad4838d7d35c4d6ea796ee12ae5aedf8"]["available"] = True


# (again, following diff)
# Remove device "2568cc4b9c1e401495d4741a5f89bee1" from anywhere
m_adam_cooling.pop("2568cc4b9c1e401495d4741a5f89bee1")

# Remove device "854f8a9b0e7e425db97f1f110e1ce4b3" from anywhere
m_adam_cooling.pop("854f8a9b0e7e425db97f1f110e1ce4b3")

# Go for 1772
m_adam_cooling["1772a4ea304041adb83f357b751341ff"]["sensors"][
    "temperature"
] = 21.6

# Go for e2f4
m_adam_cooling["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "setpoint"
] = 23.5
m_adam_cooling["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "temperature"
] = 23.9
m_adam_cooling["f871b8c4d63549319221e294e4f88074"]["thermostat"][
    "setpoint"
] = 25.0
m_adam_cooling["f871b8c4d63549319221e294e4f88074"]["sensors"][
    "temperature"
] = 23.9
m_adam_cooling["f871b8c4d63549319221e294e4f88074"][
    "control_state"
] = "cooling"
m_adam_cooling["f871b8c4d63549319221e294e4f88074"]["climate_mode"] = "auto"


# Go for da22
m_adam_cooling["da224107914542988a88561b4452b0f6"][
    "select_regulation_mode"
] = "cooling"
m_adam_cooling["da224107914542988a88561b4452b0f6"][
    "regulation_modes"
].append("cooling")
m_adam_cooling["da224107914542988a88561b4452b0f6"]["sensors"][
    "outdoor_temperature"
] = 29.65

# Go for 056e
m_adam_cooling["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"][
    "cooling_state"
] = True
m_adam_cooling["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"][
    "heating_state"
] = False
m_adam_cooling["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"][
    "flame_state"
] = False
m_adam_cooling["056ee145a816487eaa69243c3280f8bf"]["sensors"][
    "water_temperature"
] = 19.0
m_adam_cooling["056ee145a816487eaa69243c3280f8bf"]["sensors"][
    "intended_boiler_temperature"
] = 17.5

json_writer("m_adam_cooling", m_adam_cooling)

### FROM ABOVE

m_adam_heating = m_adam_cooling.copy()

# Correct setpoint for "ad4838d7d35c4d6ea796ee12ae5aedf8"
m_adam_heating["f2bf9048bef64cc5b6d5110154e33c81"]["thermostat"][
    "setpoint"
] = 20.0
m_adam_heating["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "setpoint"
] = 20.0
m_adam_heating["f2bf9048bef64cc5b6d5110154e33c81"]["sensors"][
    "temperature"
] = 19.1
m_adam_heating["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "temperature"
] = 19.1

m_adam_heating["f2bf9048bef64cc5b6d5110154e33c81"][
    "control_state"
] = "preheating"
m_adam_heating["f2bf9048bef64cc5b6d5110154e33c81"]["climate_mode"] = "heat"

# Go for 1772
m_adam_heating["1772a4ea304041adb83f357b751341ff"]["sensors"][
    "temperature"
] = 18.6
# Related zone temperature is set below

# Go for e2f4
m_adam_heating["f871b8c4d63549319221e294e4f88074"]["thermostat"][
    "setpoint"
] = 15.0
m_adam_heating["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "setpoint"
] = 15.0
m_adam_heating["f871b8c4d63549319221e294e4f88074"]["sensors"][
    "temperature"
] = 17.9
m_adam_heating["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "temperature"
] = 17.9

m_adam_heating["f871b8c4d63549319221e294e4f88074"]["climate_mode"] = "auto"
m_adam_heating["f871b8c4d63549319221e294e4f88074"][
    "control_state"
] = "idle"

# Go for da22
m_adam_heating["da224107914542988a88561b4452b0f6"][
    "select_regulation_mode"
] = "heating"
m_adam_heating["da224107914542988a88561b4452b0f6"][
    "regulation_modes"
].remove("cooling")
m_adam_heating["da224107914542988a88561b4452b0f6"]["sensors"][
    "outdoor_temperature"
] = -1.25

# Go for 056e
m_adam_heating["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"].pop(
    "cooling_state"
)
m_adam_heating["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"][
    "heating_state"
] = True
m_adam_heating["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"][
    "flame_state"
] = False
m_adam_heating["056ee145a816487eaa69243c3280f8bf"]["sensors"][
    "water_temperature"
] = 37.0
m_adam_heating["056ee145a816487eaa69243c3280f8bf"]["sensors"][
    "intended_boiler_temperature"
] = 38.1
m_adam_heating["056ee145a816487eaa69243c3280f8bf"]["max_dhw_temperature"] = {
    "setpoint": 60.0,
    "lower_bound": 40.0,
    "upper_bound": 60.0,
    "resolution": 0.01,
}

json_writer("m_adam_heating", m_adam_heating)

### Manual Anna fixtures

base_anna_manual = "anna_heatpump_heating"
basefile = f"./fixtures/{base_anna_manual}/data.json"

io = open(basefile)
base = json.load(io)
m_anna_heatpump_cooling = base.copy()

# Go for 1cbf
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"][
    "model"
] = "Generic heater/cooler"
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"][
    "binary_sensors"
]["cooling_enabled"] = True
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"][
    "binary_sensors"
]["heating_state"] = False
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"][
    "binary_sensors"
]["cooling_state"] = True

m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "water_temperature"
] = 22.7
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "dhw_temperature"
] = 41.5
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "intended_boiler_temperature"
] = 0.0
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "modulation_level"
] = 40
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "return_temperature"
] = 23.8
m_anna_heatpump_cooling["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "outdoor_air_temperature"
] = 28.0

# Go for 015a
m_anna_heatpump_cooling["015ae9ea3f964e668e490fa39da3870b"]["sensors"][
    "outdoor_temperature"
] = 28.2

# Go for 3cb7
m_anna_heatpump_cooling["3cb70739631c4d17a86b8b12e8a5161b"]["control_state"] = "cooling"
m_anna_heatpump_cooling["3cb70739631c4d17a86b8b12e8a5161b"]["thermostat"][
    "setpoint_low"
] = 20.5
m_anna_heatpump_cooling["3cb70739631c4d17a86b8b12e8a5161b"]["thermostat"][
    "setpoint_high"
] = 30.0

m_anna_heatpump_cooling["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "temperature"
] = 26.3
m_anna_heatpump_cooling["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "setpoint_low"
] = 20.5
m_anna_heatpump_cooling["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "setpoint_high"
] = 30.0

json_writer("m_anna_heatpump_cooling", m_anna_heatpump_cooling)

### FROM ABOVE

m_anna_heatpump_idle = m_anna_heatpump_cooling.copy()

# Go for 1cbf
m_anna_heatpump_idle["1cbf783bb11e4a7c8a6843dee3a86927"]["binary_sensors"][
    "compressor_state"
] = False
m_anna_heatpump_idle["1cbf783bb11e4a7c8a6843dee3a86927"]["binary_sensors"][
    "cooling_state"
] = False

m_anna_heatpump_idle["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "water_temperature"
] = 19.1
m_anna_heatpump_idle["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "dhw_temperature"
] = 46.3
m_anna_heatpump_idle["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "intended_boiler_temperature"
] = 18.0
m_anna_heatpump_idle["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "modulation_level"
] = 0
m_anna_heatpump_idle["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "return_temperature"
] = 22.0
m_anna_heatpump_idle["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "outdoor_air_temperature"
] = 28.2


# Go for 3cb7
m_anna_heatpump_idle["3cb70739631c4d17a86b8b12e8a5161b"]["control_state"] = "idle"
m_anna_heatpump_idle["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "temperature"
] = 23.0
m_anna_heatpump_idle["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "cooling_activation_outdoor_temperature"
] = 25.0

json_writer("m_anna_heatpump_idle", m_anna_heatpump_idle)
