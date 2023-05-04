#!/usr/bin/env python3
"""Generate fake fixtures from existing fixtures."""

import json
import os

print("... Crafting m_* fixtures from userdata ...")  # noqa: T201

### ADAM

base_adam_fake = "adam_plus_anna_new"
basefile = f"./fixtures/{base_adam_fake}/all_data.json"
basefile_n = f"./fixtures/{base_adam_fake}/notifications.json"

io = open(basefile)
base = json.load(io)
io_n = open(basefile_n)
base_n = json.load(io_n)

m_adam_cooling = base.copy()

# Set cooling_present to true
m_adam_cooling["gateway"]["cooling_present"] = True

# Remove device "67d73d0bd469422db25a618a5fb8eeb0" from anywhere
m_adam_cooling["devices"].pop("67d73d0bd469422db25a618a5fb8eeb0")

# Remove setpoint for "ad4838d7d35c4d6ea796ee12ae5aedf8" and inject low and high
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["thermostat"].pop(
    "setpoint"
)
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["thermostat"][
    "setpoint_low"
] = 4.0
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["thermostat"][
    "setpoint_high"
] = 23.5

# Add new key available
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["available"] = True

m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"][
    "selected_schedule"
] = "None"
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"][
    "control_state"
] = "cooling"
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["mode"] = "heat_cool"

# (following diff, now 2954 is removed)
# Remove device "29542b2b6a6a4169acecc15c72a599b8" from anywhere
m_adam_cooling["devices"].pop("29542b2b6a6a4169acecc15c72a599b8")

# Back at ad48
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"].pop("setpoint")
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "temperature"
] = 25.8
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "setpoint_low"
] = 4.0
m_adam_cooling["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "setpoint_high"
] = 23.5

# (again, following diff)
# Remove device "2568cc4b9c1e401495d4741a5f89bee1" from anywhere
m_adam_cooling["devices"].pop("2568cc4b9c1e401495d4741a5f89bee1")
# Remove device "854f8a9b0e7e425db97f1f110e1ce4b3" from anywhere
m_adam_cooling["devices"].pop("854f8a9b0e7e425db97f1f110e1ce4b3")

# Go for 1772
m_adam_cooling["devices"]["1772a4ea304041adb83f357b751341ff"]["sensors"].pop("setpoint")
m_adam_cooling["devices"]["1772a4ea304041adb83f357b751341ff"]["sensors"][
    "temperature"
] = 21.6

# Go for e2f4
m_adam_cooling["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["thermostat"].pop(
    "setpoint"
)
m_adam_cooling["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["thermostat"][
    "setpoint_low"
] = 19.0
m_adam_cooling["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["thermostat"][
    "setpoint_high"
] = 25.0

m_adam_cooling["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"].pop("setpoint")
m_adam_cooling["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "temperature"
] = 239
# didn't change
# m_adam_cooling["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"]["battery"] = 56
m_adam_cooling["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "setpoint_low"
] = 20.0
m_adam_cooling["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "setpoint_high"
] = 23.5


# Go for da22
m_adam_cooling["devices"]["da224107914542988a88561b4452b0f6"][
    "regulation_mode"
] = "cooling"
m_adam_cooling["devices"]["da224107914542988a88561b4452b0f6"][
    "regulation_modes"
].append("cooling")
m_adam_cooling["devices"]["da224107914542988a88561b4452b0f6"]["sensors"][
    "outdoor_temperature"
] = 29.65

# Go for 056e
m_adam_cooling["devices"]["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"][
    "cooling_state"
] = True
m_adam_cooling["devices"]["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"][
    "heating_state"
] = False
m_adam_cooling["devices"]["056ee145a816487eaa69243c3280f8bf"]["sensors"][
    "water_temperature"
] = 19.0
m_adam_cooling["devices"]["056ee145a816487eaa69243c3280f8bf"]["sensors"][
    "intended_boiler_temperature"
] = 17.5

fake_name = "m_adam_cooling"

if not os.path.exists(f"./fixtures/{fake_name}"):
    os.makedirs(f"./fixtures/{fake_name}")

outfile = f"./fixtures/{fake_name}/all_data.json"
data = json.dumps(m_adam_cooling, indent=2)
with open(outfile, "w") as f:
    f.write(data)

outfile = f"./fixtures/{fake_name}/notifications.json"
data = json.dumps(base_n, indent=2)
with open(outfile, "w") as f:
    f.write(data)


### FROM ABOVE

m_adam_heating = m_adam_cooling.copy()

# Set cooling_present to true
m_adam_cooling["gateway"]["cooling_present"] = False

# Remove setpoint for "ad4838d7d35c4d6ea796ee12ae5aedf8" and inject low and high
m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["thermostat"][
    "setpoint"
] = 20.0
m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["thermostat"].pop(
    "setpoint_low"
)
m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["thermostat"].pop(
    "setpoint_high"
)

m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"][
    "control_state"
] = "heating"
m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["mode"] = "heat"

# Back at ad48
m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "setpoint"
] = 20.0
m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"][
    "temperature"
] = 19.1
m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"].pop(
    "setpoint_low"
)
m_adam_heating["devices"]["ad4838d7d35c4d6ea796ee12ae5aedf8"]["sensors"].pop(
    "setpoint_high"
)

# Go for 1772
m_adam_heating["devices"]["1772a4ea304041adb83f357b751341ff"]["sensors"][
    "temperature"
] = 18.6

# Go for e2f4
m_adam_heating["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["thermostat"][
    "setpoint"
] = 15.0
m_adam_heating["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["thermostat"].pop(
    "setpoint_low"
)
m_adam_heating["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["thermostat"].pop(
    "setpoint_high"
)

m_adam_heating["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "setpoint"
] = 15.0
m_adam_heating["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"][
    "temperature"
] = 17.9
# m_adam_heating["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"]["battery"] = 56
m_adam_heating["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"].pop(
    "setpoint_low"
)
m_adam_heating["devices"]["e2f4322d57924fa090fbbc48b3a140dc"]["sensors"].pop(
    "setpoint_high"
)


# Go for da22
m_adam_heating["devices"]["da224107914542988a88561b4452b0f6"][
    "regulation_mode"
] = "heating"
m_adam_heating["devices"]["da224107914542988a88561b4452b0f6"][
    "regulation_modes"
].remove("cooling")
m_adam_heating["devices"]["da224107914542988a88561b4452b0f6"]["sensors"][
    "outdoor_temperature"
] = -1.25

# Go for 056e
m_adam_heating["devices"]["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"].pop(
    "cooling_state"
)
m_adam_heating["devices"]["056ee145a816487eaa69243c3280f8bf"]["binary_sensors"][
    "heating_state"
] = True
m_adam_heating["devices"]["056ee145a816487eaa69243c3280f8bf"]["sensors"][
    "water_temperature"
] = 37.0
m_adam_heating["devices"]["056ee145a816487eaa69243c3280f8bf"]["sensors"][
    "intended_boiler_temperature"
] = 38.1
m_adam_heating["devices"]["056ee145a816487eaa69243c3280f8bf"]["max_dhw_temperature"] = {
    "setpoint": 60.0,
    "lower_bound": 40.0,
    "upper_bound": 60.0,
    "resolution": 0.01,
}

fake_name = "m_adam_heating"

if not os.path.exists(f"./fixtures/{fake_name}"):
    os.makedirs(f"./fixtures/{fake_name}")

outfile = f"./fixtures/{fake_name}/all_data.json"
data = json.dumps(m_adam_heating, indent=2)
with open(outfile, "w") as f:
    f.write(data)

outfile = f"./fixtures/{fake_name}/notifications.json"
data = json.dumps(base_n, indent=2)
with open(outfile, "w") as f:
    f.write(data)

### ANNA

base_anna_fake = "anna_heatpump_heating"
basefile = f"./fixtures/{base_anna_fake}/all_data.json"
basefile_n = f"./fixtures/{base_anna_fake}/notifications.json"

io = open(basefile)
base = json.load(io)
io_n = open(basefile_n)
base_n = json.load(io_n)

m_anna_heatpump_cooling = base.copy()

# Set cooling_present to true
m_anna_heatpump_cooling["gateway"]["cooling_present"] = True

# Go for 1cbf
m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"][
    "model"
] = "Generic heater/cooler"

m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"][
    "binary_sensors"
]["cooling_enabled"] = True
m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"][
    "binary_sensors"
]["heating_state"] = False
m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"][
    "binary_sensors"
]["cooling_state"] = True

m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "water_temperature"
] = 22.7
m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "dhw_temperature"
] = 41.5
m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "intended_boiler_temperature"
] = 0.0
m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "modulation_level"
] = 40
m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "return_temperature"
] = 23.8
m_anna_heatpump_cooling["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "outdoor_air_temperature"
] = 28.0


# Go for 015a
m_anna_heatpump_cooling["devices"]["015ae9ea3f964e668e490fa39da3870b"]["sensors"][
    "outdoor_temperature"
] = 28.2

# Go for 3cb7
m_anna_heatpump_cooling["devices"]["3cb70739631c4d17a86b8b12e8a5161b"][
    "thermostat"
].pop("setpoint")
m_anna_heatpump_cooling["devices"]["3cb70739631c4d17a86b8b12e8a5161b"]["thermostat"][
    "setpoint_low"
] = 20.5
m_anna_heatpump_cooling["devices"]["3cb70739631c4d17a86b8b12e8a5161b"]["thermostat"][
    "setpoint_high"
] = 24.0

m_anna_heatpump_cooling["devices"]["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"].pop(
    "setpoint"
)
m_anna_heatpump_cooling["devices"]["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "temperature"
] = 26.3
m_anna_heatpump_cooling["devices"]["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "setpoint_low"
] = 20.5
m_anna_heatpump_cooling["devices"]["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "setpoint_high"
] = 24.0

fake_name = "m_anna_heatpump_cooling"

if not os.path.exists(f"./fixtures/{fake_name}"):
    os.makedirs(f"./fixtures/{fake_name}")

outfile = f"./fixtures/{fake_name}/all_data.json"
data = json.dumps(m_anna_heatpump_cooling, indent=2)
with open(outfile, "w") as f:
    f.write(data)

outfile = f"./fixtures/{fake_name}/notifications.json"
data = json.dumps(base_n, indent=2)
with open(outfile, "w") as f:
    f.write(data)


### FROM ABOVE

m_anna_heatpump_idle = m_anna_heatpump_cooling.copy()

# Go for 1cbf
m_anna_heatpump_idle["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["binary_sensors"][
    "compressor_state"
] = False
m_anna_heatpump_idle["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["binary_sensors"][
    "cooling_state"
] = False

m_anna_heatpump_idle["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "water_temperature"
] = 19.1
m_anna_heatpump_idle["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "dhw_temperature"
] = 46.3
m_anna_heatpump_idle["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "intended_boiler_temperature"
] = 18.0
m_anna_heatpump_idle["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "modulation_level"
] = 0
m_anna_heatpump_idle["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "return_temperature"
] = 22.0
m_anna_heatpump_idle["devices"]["1cbf783bb11e4a7c8a6843dee3a86927"]["sensors"][
    "outdoor_air_temperature"
] = 28.2


# Go for 3cb7

m_anna_heatpump_idle["devices"]["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "temperature"
] = 23.0
m_anna_heatpump_idle["devices"]["3cb70739631c4d17a86b8b12e8a5161b"]["sensors"][
    "cooling_activation_outdoor_temperature"
] = 25.0

fake_name = "m_anna_heatpump_idle"

if not os.path.exists(f"./fixtures/{fake_name}"):
    os.makedirs(f"./fixtures/{fake_name}")

outfile = f"./fixtures/{fake_name}/all_data.json"
data = json.dumps(m_anna_heatpump_idle, indent=2)
with open(outfile, "w") as f:
    f.write(data)

outfile = f"./fixtures/{fake_name}/notifications.json"
data = json.dumps(base_n, indent=2)
with open(outfile, "w") as f:
    f.write(data)
