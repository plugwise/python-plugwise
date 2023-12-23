"""Test Plugwise module combined Adam and Anna/Jip related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise


class TestPlugwiseGeneric(
    TestPlugwise
):  # pylint: disable=attribute-defined-outside-init
    """Tests for Adam combined, i.e. Anna or Jip."""

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna(self):
        """Test Adam (firmware 3.0) with Anna setup."""
        testdata = {
            "2743216f626f43948deec1f7ab3b3d70": {
                "dev_class": "heater_central",
                "location": "07d618f0bb80412687f065b8698ce3e7",
                "model": "Generic heater",
                "name": "OpenTherm",
                "maximum_boiler_temperature": {
                    "setpoint": 80.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": False,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 47.0,
                    "intended_boiler_temperature": 0.0,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "aa6b0002df0a46e1b1eb94beb61eddfe": {
                "dev_class": "hometheater",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "45d410adf8fd461e85cebf16d5ead542",
                "model": "Plug",
                "name": "MediaCenter",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 10.3,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "b128b4bbbd1f47e9bf4d756e8fb5ee94": {
                "dev_class": "gateway",
                "firmware": "3.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "07d618f0bb80412687f065b8698ce3e7",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "select_regulation_mode": "heating",
                "binary_sensors": {"plugwise_notification": True},
                "sensors": {"outdoor_temperature": 11.9},
            },
            "ee62cad889f94e8ca3d09021f03a660b": {
                "dev_class": "thermostat",
                "location": "009490cc2f674ce6b576863fbb64f867",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 1.0,
                    "upper_bound": 35.0,
                    "resolution": 0.01,
                },
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["Weekschema", "off"],
                "select_schedule": "Weekschema",
                "mode": "auto",
                "sensors": {"temperature": 20.5, "setpoint": 20.5},
            },
            "f2be121e4a9345ac83c6e99ed89a98be": {
                "dev_class": "computer_desktop",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "5ccb6c41a7d9403988d261ceee04239f",
                "name": "Work-PC",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 79.8,
                    "electricity_consumed_interval": 7.03,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
        }

        self.smile_setup = "adam_plus_anna"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.15"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        assert smile.gateway_id == "b128b4bbbd1f47e9bf4d756e8fb5ee94"
        assert smile._last_active["009490cc2f674ce6b576863fbb64f867"] == "Weekschema"
        assert smile.device_items == 70
        assert "6fb89e35caeb4b1cb275184895202d84" in self.notifications

        result = await self.tinker_thermostat(
            smile, "009490cc2f674ce6b576863fbb64f867", good_schedules=["Weekschema"]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "aa6b0002df0a46e1b1eb94beb61eddfe"
        )
        assert switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        result = await self.tinker_thermostat(
            smile,
            "009490cc2f674ce6b576863fbb64f867",
            good_schedules=["Weekschema"],
            unhappy=True,
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "aa6b0002df0a46e1b1eb94beb61eddfe", unhappy=True
        )
        assert switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_copy_with_error_domain_added(self):
        """Test erroneous domain_objects file from user."""
        testdata = {
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "binary_sensors": {"heating_state": False},
            },
        }

        self.smile_setup = "adam_plus_anna_copy_with_error_domain_added"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.23"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        assert smile.device_items == 70

        assert "3d28a20e17cb47dca210a132463721d5" in self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new(self):
        """Test extended Adam (firmware 3.6) with Anna and a switch-group setup."""
        testdata = {
            "67d73d0bd469422db25a618a5fb8eeb0": {
                "dev_class": "zz_misc",
                "location": "b4f211175e124df59603412bafa77a34",
                "model": "lumi.plug.maeu01",
                "name": "SmartPlug Floor 0",
                "zigbee_mac_address": "54EF4410002C97F2",
                "vendor": "LUMI",
                "available": True,
                "sensors": {"electricity_consumed_interval": 0.0},
                "switches": {"relay": True, "lock": False},
            },
            "ad4838d7d35c4d6ea796ee12ae5aedf8": {
                "dev_class": "thermostat",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 18.5,
                    "lower_bound": 1.0,
                    "upper_bound": 35.0,
                    "resolution": 0.01,
                },
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "asleep",
                "available_schedules": ["Weekschema", "Badkamer", "Test", "off"],
                "select_schedule": "Weekschema",
                "control_state": "heating",
                "mode": "auto",
                "sensors": {"temperature": 18.1, "setpoint": 18.5},
            },
            "29542b2b6a6a4169acecc15c72a599b8": {
                "dev_class": "hometheater",
                "firmware": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Mediacenter",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.2,
                    "electricity_consumed_interval": 3.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "2568cc4b9c1e401495d4741a5f89bee1": {
                "dev_class": "computer_desktop",
                "firmware": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Werkplek",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 98.0,
                    "electricity_consumed_interval": 24.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "854f8a9b0e7e425db97f1f110e1ce4b3": {
                "dev_class": "central_heating_pump",
                "firmware": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Vloerverwarming",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 46.8,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "1772a4ea304041adb83f357b751341ff": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "f871b8c4d63549319221e294e4f88074",
                "model": "Tom/Floor",
                "name": "Tom Badkamer",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 21.6,
                    "setpoint": 15.0,
                    "battery": 99,
                    "temperature_difference": 2.3,
                    "valve_position": 0.0,
                },
            },
            "e2f4322d57924fa090fbbc48b3a140dc": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "f871b8c4d63549319221e294e4f88074",
                "model": "Lisa",
                "name": "Lisa Badkamer",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 15.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["Weekschema", "Badkamer", "Test", "off"],
                "select_schedule": "Badkamer",
                "control_state": "off",
                "mode": "auto",
                "sensors": {"temperature": 17.9, "setpoint": 15.0, "battery": 56},
            },
            "da224107914542988a88561b4452b0f6": {
                "dev_class": "gateway",
                "firmware": "3.6.4",
                "hardware": "AME Smile 2.0 board",
                "location": "bc93488efab249e5bc54fd7e175a6f91",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "select_regulation_mode": "heating",
                "regulation_modes": ["heating", "off", "bleeding_cold", "bleeding_hot"],
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": -1.25},
            },
            "056ee145a816487eaa69243c3280f8bf": {
                "dev_class": "heater_central",
                "location": "bc93488efab249e5bc54fd7e175a6f91",
                "model": "Generic heater",
                "name": "OpenTherm",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 25.0,
                    "upper_bound": 95.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": True,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 37.0,
                    "intended_boiler_temperature": 38.1,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "e8ef2a01ed3b4139a53bf749204fe6b4": {
                "dev_class": "switching",
                "model": "Switchgroup",
                "name": "Test",
                "members": [
                    "2568cc4b9c1e401495d4741a5f89bee1",
                    "29542b2b6a6a4169acecc15c72a599b8",
                ],
                "switches": {"relay": True},
            },
        }
        testdata_updated = {
            "67d73d0bd469422db25a618a5fb8eeb0": {
                "switches": {"lock": True},
            },
            "ad4838d7d35c4d6ea796ee12ae5aedf8": {
                "mode": "off",
            },
            "29542b2b6a6a4169acecc15c72a599b8": {
                "switches": {"relay": False, "lock": False},
            },
            "2568cc4b9c1e401495d4741a5f89bee1": {
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "1772a4ea304041adb83f357b751341ff": {
                "available": False,
            },
            "e2f4322d57924fa090fbbc48b3a140dc": {
                "mode": "off",
            },
            "da224107914542988a88561b4452b0f6": {
                "binary_sensors": {"plugwise_notification": True},
            },
            "e8ef2a01ed3b4139a53bf749204fe6b4": {
                "members": [
                    "2568cc4b9c1e401495d4741a5f89bee1",
                    "29542b2b6a6a4169acecc15c72a599b8",
                ],
                "switches": {"relay": False},
            },
        }

        self.smile_setup = "adam_plus_anna_new"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.6.4"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-01-16 00:00:01", testdata)
        assert smile.gateway_id == "da224107914542988a88561b4452b0f6"
        assert smile._last_active["f2bf9048bef64cc5b6d5110154e33c81"] == "Weekschema"
        assert smile._last_active["f871b8c4d63549319221e294e4f88074"] == "Badkamer"
        assert smile.device_items == 145
        assert smile.device_list == [
            "da224107914542988a88561b4452b0f6",
            "056ee145a816487eaa69243c3280f8bf",
            "67d73d0bd469422db25a618a5fb8eeb0",
            "ad4838d7d35c4d6ea796ee12ae5aedf8",
            "29542b2b6a6a4169acecc15c72a599b8",
            "2568cc4b9c1e401495d4741a5f89bee1",
            "854f8a9b0e7e425db97f1f110e1ce4b3",
            "1772a4ea304041adb83f357b751341ff",
            "e2f4322d57924fa090fbbc48b3a140dc",
            "e8ef2a01ed3b4139a53bf749204fe6b4",
        ]

        result = await self.tinker_thermostat(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            good_schedules=["Weekschema", "Badkamer", "Test"],
        )
        assert result

        # Special test-case for turning a schedule off based on only the location id.
        await smile.set_schedule_state("f2bf9048bef64cc5b6d5110154e33c81", "off")

        # Special test-case for turning a schedule off for a location via the option "off".
        await smile.set_schedule_state("f2bf9048bef64cc5b6d5110154e33c81", "on", "off")

        # bad schedule-state test
        result = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "bad",
            good_schedules=["Badkamer"],
            single=True,
        )
        assert result

        smile._schedule_old_states["f2bf9048bef64cc5b6d5110154e33c81"][
            "Badkamer"
        ] = "off"
        result_1 = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "on",
            good_schedules=["Badkamer"],
            single=True,
        )
        result_2 = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "on",
            good_schedules=["Badkamer"],
            single=True,
        )
        assert result_1 and result_2

        switch_change = await self.tinker_switch(
            smile,
            "e8ef2a01ed3b4139a53bf749204fe6b4",
            ["2568cc4b9c1e401495d4741a5f89bee1", "29542b2b6a6a4169acecc15c72a599b8"],
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "056ee145a816487eaa69243c3280f8bf", model="dhw_cm_switch"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "854f8a9b0e7e425db97f1f110e1ce4b3", model="lock"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "2568cc4b9c1e401495d4741a5f89bee1"
        )
        assert not switch_change

        await self.tinker_regulation_mode(smile)

        await self.tinker_max_boiler_temp(smile)

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        self.smile_setup = "updated/adam_plus_anna_new"
        await self.device_test(
            smile, "2022-01-16 00:00:01", testdata_updated, initialize=False
        )

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_plus_jip(self):
        """Test Adam with Jip setup."""
        testdata = {
            "e4684553153b44afbef2200885f379dc": {
                "dev_class": "heater_central",
                "location": "9e4433a9d69f40b3aefd15e74395eaec",
                "model": "10.20",
                "name": "OpenTherm",
                "vendor": "Remeha B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 90.0,
                    "lower_bound": 20.0,
                    "upper_bound": 90.0,
                    "resolution": 0.01,
                },
                "max_dhw_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 40.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 37.3,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 37.1,
                    "water_pressure": 1.4,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "a6abc6a129ee499c88a4d420cc413b47": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "d58fec52899f4f1c92e4f8fad6d8c48c",
                "model": "Lisa",
                "name": "Logeerkamer",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["None"],
                "select_schedule": "None",
                "control_state": "off",
                "mode": "heat",
                "sensors": {"temperature": 30.0, "setpoint": 13.0, "battery": 80},
            },
            "1346fbd8498d4dbcab7e18d51b771f3d": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "06aecb3d00354375924f50c47af36bd2",
                "model": "Lisa",
                "name": "Slaapkamer",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "no_frost",
                "available_schedules": ["None"],
                "select_schedule": "None",
                "control_state": "off",
                "mode": "heat",
                "sensors": {"temperature": 24.2, "setpoint": 13.0, "battery": 92},
            },
            "833de10f269c4deab58fb9df69901b4e": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "13228dab8ce04617af318a2888b3c548",
                "model": "Tom/Floor",
                "name": "Tom Woonkamer",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 24.0,
                    "setpoint": 9.0,
                    "temperature_difference": 1.8,
                    "valve_position": 100,
                },
            },
            "6f3e9d7084214c21b9dfa46f6eeb8700": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "d27aede973b54be484f6842d1b2802ad",
                "model": "Lisa",
                "name": "Kinderkamer",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["None"],
                "select_schedule": "None",
                "control_state": "off",
                "mode": "heat",
                "sensors": {"temperature": 30.0, "setpoint": 13.0, "battery": 79},
            },
            "f61f1a2535f54f52ad006a3d18e459ca": {
                "dev_class": "zone_thermometer",
                "firmware": "2020-09-01T02:00:00+02:00",
                "hardware": "1",
                "location": "13228dab8ce04617af318a2888b3c548",
                "model": "Jip",
                "name": "Woonkamer",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 9.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["None"],
                "select_schedule": "None",
                "control_state": "off",
                "mode": "heat",
                "sensors": {
                    "temperature": 27.4,
                    "setpoint": 9.0,
                    "battery": 100,
                    "humidity": 56.2,
                },
            },
            "d4496250d0e942cfa7aea3476e9070d5": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "d27aede973b54be484f6842d1b2802ad",
                "model": "Tom/Floor",
                "name": "Tom Kinderkamer",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 28.7,
                    "setpoint": 13.0,
                    "temperature_difference": 1.9,
                    "valve_position": 0.0,
                },
            },
            "356b65335e274d769c338223e7af9c33": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "06aecb3d00354375924f50c47af36bd2",
                "model": "Tom/Floor",
                "name": "Tom Slaapkamer",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 24.3,
                    "setpoint": 13.0,
                    "temperature_difference": 1.7,
                    "valve_position": 0.0,
                },
            },
            "b5c2386c6f6342669e50fe49dd05b188": {
                "dev_class": "gateway",
                "firmware": "3.2.8",
                "hardware": "AME Smile 2.0 board",
                "location": "9e4433a9d69f40b3aefd15e74395eaec",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "select_regulation_mode": "heating",
                "regulation_modes": ["heating", "off", "bleeding_cold", "bleeding_hot"],
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 24.9},
            },
            "1da4d325838e4ad8aac12177214505c9": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "d58fec52899f4f1c92e4f8fad6d8c48c",
                "model": "Tom/Floor",
                "name": "Tom Logeerkamer",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 28.8,
                    "setpoint": 13.0,
                    "temperature_difference": 2.0,
                    "valve_position": 0.0,
                },
            },
            "457ce8414de24596a2d5e7dbc9c7682f": {
                "dev_class": "zz_misc",
                "location": "9e4433a9d69f40b3aefd15e74395eaec",
                "model": "lumi.plug.maeu01",
                "name": "Plug",
                "zigbee_mac_address": "ABCD012345670A06",
                "vendor": "LUMI",
                "available": True,
                "sensors": {"electricity_consumed_interval": 0.0},
                "switches": {"relay": False, "lock": True},
            },
        }

        self.smile_setup = "adam_jip"
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, "2021-06-20 00:00:01", testdata)
        assert smile.gateway_id == "b5c2386c6f6342669e50fe49dd05b188"
        assert smile._last_active["d58fec52899f4f1c92e4f8fad6d8c48c"] is None
        assert smile._last_active["06aecb3d00354375924f50c47af36bd2"] is None
        assert smile._last_active["d27aede973b54be484f6842d1b2802ad"] is None
        assert smile._last_active["13228dab8ce04617af318a2888b3c548"] is None
        assert smile.device_items == 219

        # Negative test
        result = await self.tinker_thermostat(
            smile,
            "13228dab8ce04617af318a2888b3c548",
            schedule_on=False,
            good_schedules=[None],
        )
        assert result

        result = await self.tinker_thermostat_schedule(
            smile,
            "13228dab8ce04617af318a2888b3c548",
            "off",
            good_schedules=[None],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)
