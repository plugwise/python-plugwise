"""Test Plugwise module Anna related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise, pw_exceptions


class TestPlugwiseAnna(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for Anna standalone, i.e. not combined with Adam."""

    @pytest.mark.asyncio
    async def test_connect_legacy_anna(self):
        """Test a legacy Anna device."""
        testdata = {
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "dev_class": "gateway",
                "firmware": "1.8.22",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "mac_address": "01:23:45:67:89:AB",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "0d266432d64443e283b5d708ae98b455": {
                "dev_class": "thermostat",
                "firmware": "2017-03-13T11:54:58+01:00",
                "hardware": "6539-1301-500",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "vacation", "asleep", "home", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["Thermostat schedule"],
                "select_schedule": "Thermostat schedule",
                "mode": "auto",
                "sensors": {"temperature": 20.4, "illuminance": 151, "setpoint": 20.5},
            },
            "04e4cbfe7f4340f090f85ec3b9e6a950": {
                "dev_class": "heater_central",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "4.21",
                "name": "OpenTherm",
                "vendor": "Bosch Thermotechniek B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 50.0,
                    "lower_bound": 50.0,
                    "upper_bound": 90.0,
                    "resolution": 1.0,
                },
                "binary_sensors": {"flame_state": True, "heating_state": True},
                "sensors": {
                    "water_temperature": 23.6,
                    "intended_boiler_temperature": 17.0,
                    "modulation_level": 0.0,
                    "return_temperature": 21.7,
                    "water_pressure": 1.2,
                },
            },
        }

        self.smile_setup = "legacy_anna"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "1.8.22"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        assert smile.gateway_id == "0000aaaa0000aaaa0000aaaa0000aa00"
        assert (
            smile._last_active["0000aaaa0000aaaa0000aaaa0000aa00"]
            == "Thermostat schedule"
        )
        assert smile.device_items == 44
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "0000aaaa0000aaaa0000aaaa0000aa00",
            good_schedules=[
                "Thermostat schedule",
            ],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        result = await self.tinker_thermostat(
            smile,
            "0000aaaa0000aaaa0000aaaa0000aa00",
            good_schedules=[
                "Thermostat schedule",
            ],
            unhappy=True,
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_legacy_anna_2(self):
        """Test another legacy Anna device."""
        testdata = {
            "be81e3f8275b4129852c4d8d550ae2eb": {
                "dev_class": "gateway",
                "firmware": "1.8.22",
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "mac_address": "01:23:45:67:89:AB",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 21.0},
            },
            "9e7377867dc24e51b8098a5ba02bd89d": {
                "dev_class": "thermostat",
                "firmware": "2017-03-13T11:54:58+01:00",
                "hardware": "6539-1301-5002",
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 15.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["vacation", "away", "no_frost", "home", "asleep"],
                "active_preset": None,
                "available_schedules": ["Thermostat schedule"],
                "select_schedule": "None",
                "mode": "heat",
                "sensors": {"temperature": 21.4, "illuminance": 19.5, "setpoint": 15.0},
            },
            "ea5d8a7177e541b0a4b52da815166de4": {
                "dev_class": "heater_central",
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "model": "Generic heater",
                "name": "OpenTherm",
                "maximum_boiler_temperature": {
                    "setpoint": 70.0,
                    "lower_bound": 50.0,
                    "upper_bound": 90.0,
                    "resolution": 1.0,
                },
                "binary_sensors": {"flame_state": False, "heating_state": False},
                "sensors": {
                    "water_temperature": 54.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 0.0,
                    "water_pressure": 1.7,
                },
            },
        }

        self.smile_setup = "legacy_anna_2"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "1.8.22"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, "2020-05-03 00:00:01", testdata)

        assert smile.gateway_id == "be81e3f8275b4129852c4d8d550ae2eb"
        assert (
            smile._last_active["be81e3f8275b4129852c4d8d550ae2eb"]
            == "Thermostat schedule"
        )
        assert smile.device_items == 44
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            good_schedules=[
                "Thermostat schedule",
            ],
        )
        assert result

        smile._schedule_old_states["be81e3f8275b4129852c4d8d550ae2eb"][
            "Thermostat schedule"
        ] = "off"
        result_1 = await self.tinker_thermostat_schedule(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            "on",
            good_schedules=["Thermostat schedule"],
            single=True,
        )
        result_2 = await self.tinker_thermostat_schedule(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            "on",
            good_schedules=["Thermostat schedule"],
            single=True,
        )
        assert result_1 and result_2

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4(self):
        """Test an Anna firmware 4 setup."""
        testdata = {
            "cd0e6156b1f04d5f952349ffbe397481": {
                "dev_class": "heater_central",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "model": "2.32",
                "name": "OpenTherm",
                "vendor": "Bosch Thermotechniek B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 70.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "max_dhw_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 30.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": True,
                    "flame_state": True,
                },
                "sensors": {
                    "water_temperature": 52.0,
                    "intended_boiler_temperature": 48.6,
                    "modulation_level": 0.0,
                    "return_temperature": 42.0,
                    "water_pressure": 2.1,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "eb5309212bf5407bb143e5bfa3b18aee",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["vacation", "no_frost", "away", "asleep", "home"],
                "active_preset": "home",
                "available_schedules": ["Standaard", "Thuiswerken", "off"],
                "select_schedule": "off",
                "mode": "heat",
                "sensors": {"temperature": 20.5, "setpoint": 20.5, "illuminance": 40.5},
            },
            "0466eae8520144c78afb29628384edeb": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 7.44},
            },
        }
        testdata_updated = {
            "cd0e6156b1f04d5f952349ffbe397481": {
                "maximum_boiler_temperature": {
                    "setpoint": 69.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "max_dhw_temperature": {
                    "setpoint": 59.0,
                    "lower_bound": 30.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 51.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 41.0,
                    "water_pressure": 2.1,
                },
                "switches": {"dhw_cm_switch": True},
            },
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "thermostat": {
                    "setpoint": 19.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "active_preset": "away",
                "select_schedule": "Standaard",
                "mode": "auto",
                "sensors": {"temperature": 19.5, "setpoint": 19.5, "illuminance": 39.5},
            },
            "0466eae8520144c78afb29628384edeb": {
                "sensors": {"outdoor_temperature": 6.44},
            },
        }

        self.smile_setup = "anna_v4"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-04-05 00:00:01", testdata)
        assert smile.gateway_id == "0466eae8520144c78afb29628384edeb"
        assert smile._last_active["eb5309212bf5407bb143e5bfa3b18aee"] == "Standaard"
        assert smile.device_items == 56
        assert not self.notifications

        assert not smile._cooling_present
        assert not smile._cooling_active
        assert not smile._cooling_enabled

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        result = await self.tinker_temp_offset(
            smile, "01b85360fdd243d0aaad4d6ac2a5ba7e"
        )
        assert result
        result = await self.tinker_temp_offset(
            smile, "0466eae8520144c78afb29628384edeb"
        )
        assert not result

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        self.smile_setup = "updated/anna_v4"
        await self.device_test(
            smile, "2020-04-05 00:00:01", testdata_updated, initialize=False
        )

        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        # Reset self.smile_setup
        self.smile_setup = "anna_v4"
        await self.device_test(smile, "2020-04-05 00:00:01", testdata)
        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
            unhappy=True,
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_dhw(self):
        """Test an Anna firmware 4 setup for domestic hot water."""
        testdata = {
            "cd0e6156b1f04d5f952349ffbe397481": {
                "dev_class": "heater_central",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "model": "2.32",
                "name": "OpenTherm",
                "vendor": "Bosch Thermotechniek B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 70.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "max_dhw_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 30.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": True,
                    "heating_state": False,
                    "flame_state": True,
                },
                "sensors": {
                    "water_temperature": 52.0,
                    "intended_boiler_temperature": 48.6,
                    "modulation_level": 0.0,
                    "return_temperature": 42.0,
                    "water_pressure": 2.1,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "eb5309212bf5407bb143e5bfa3b18aee",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["vacation", "no_frost", "away", "asleep", "home"],
                "active_preset": "home",
                "available_schedules": ["Standaard", "Thuiswerken", "off"],
                "select_schedule": "off",
                "mode": "heat",
                "sensors": {"temperature": 20.5, "setpoint": 20.5, "illuminance": 40.5},
            },
            "0466eae8520144c78afb29628384edeb": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 7.44},
            },
        }

        self.smile_setup = "anna_v4_dhw"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-04-05 00:00:01", testdata)
        assert smile._last_active["eb5309212bf5407bb143e5bfa3b18aee"] == "Standaard"
        assert smile.device_items == 56
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_no_tag(self):
        """Test an Anna firmware 4 setup - missing tag (issue)."""
        testdata = {
            # Anna
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "active_preset": "home",
            }
        }
        self.smile_setup = "anna_v4_no_tag"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-04-05 00:00:01", testdata)
        assert smile.device_items == 56

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw441(self):
        """Test an Anna with firmware 4.4, without a boiler."""
        testdata = {
            "a270735e4ccd45239424badc0578a2b1": {
                "dev_class": "gateway",
                "firmware": "4.4.1",
                "hardware": "AME Smile 2.0 board",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "mac_address": "D40FB200FA1C",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 8.31},
            },
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "c34c6864216446528e95d88985e714cc",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 19.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["no_frost", "asleep", "away", "vacation", "home"],
                "active_preset": "home",
                "available_schedules": ["Test", "Normaal", "off"],
                "select_schedule": "Normaal",
                "mode": "auto",
                "sensors": {"temperature": 19.1, "setpoint": 19.0, "illuminance": 0.25},
            },
            "c46b4794d28149699eacf053deedd003": {
                "dev_class": "heater_central",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "model": "Unknown",
                "name": "OnOff",
                "binary_sensors": {"heating_state": False},
            },
        }

        self.smile_setup = "anna_without_boiler_fw441"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.4.1"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile._last_active["c34c6864216446528e95d88985e714cc"] == "Normaal"
        assert smile.device_items == 38
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schedules=["Normaal"]
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_heating(self):
        """Test an Anna with Elga, cooling-mode off, in heating mode."""
        testdata = {
            "015ae9ea3f964e668e490fa39da3870b": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 20.2},
            },
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "dev_class": "heater_central",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "model": "Generic heater/cooler",
                "name": "OpenTherm",
                "vendor": "Techneco",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "max_dhw_temperature": {
                    "setpoint": 53.0,
                    "lower_bound": 35.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": True,
                    "compressor_state": True,
                    "cooling_state": False,
                    "cooling_enabled": False,
                    "slave_boiler_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 29.1,
                    "dhw_temperature": 46.3,
                    "intended_boiler_temperature": 35.0,
                    "modulation_level": 52,
                    "return_temperature": 25.1,
                    "water_pressure": 1.57,
                    "outdoor_air_temperature": 3.0,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "3cb70739631c4d17a86b8b12e8a5161b": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "c784ee9fdab44e1395b8dee7d7a497d5",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "temperature_offset": {
                    "lower_bound": -2.0,
                    "resolution": 0.1,
                    "upper_bound": 2.0,
                    "setpoint": -0.5,
                },
                "thermostat": {
                    "setpoint_low": 20.5,
                    "setpoint_high": 30.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["no_frost", "home", "away", "asleep", "vacation"],
                "active_preset": "home",
                "available_schedules": ["standaard", "off"],
                "select_schedule": "standaard",
                "mode": "auto",
                "sensors": {
                    "temperature": 19.3,
                    "illuminance": 86.0,
                    "cooling_activation_outdoor_temperature": 21.0,
                    "cooling_deactivation_threshold": 4.0,
                    "setpoint_low": 20.5,
                    "setpoint_high": 30.0,
                },
            },
        }
        testdata_updated = {
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "dev_class": "heater_central",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "model": "Generic heater/cooler",
                "name": "OpenTherm",
                "vendor": "Techneco",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": True,
                    "compressor_state": True,
                    "cooling_state": False,
                    "cooling_enabled": False,
                    "slave_boiler_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 29.1,
                    "domestic_hot_water_setpoint": 60.0,
                    "dhw_temperature": 46.3,
                    "intended_boiler_temperature": 35.0,
                    "modulation_level": 52,
                    "return_temperature": 25.1,
                    "water_pressure": 1.57,
                    "outdoor_air_temperature": 3.0,
                },
                "switches": {"dhw_cm_switch": False},
            },
        }

        self.smile_setup = "anna_heatpump_heating"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-04-12 00:00:01", testdata)
        assert smile.gateway_id == "015ae9ea3f964e668e490fa39da3870b"
        assert smile._last_active["c784ee9fdab44e1395b8dee7d7a497d5"] == "standaard"
        assert smile.device_items == 66
        assert not self.notifications
        assert self.cooling_present
        assert not smile._cooling_enabled
        assert not smile._cooling_active

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                smile,
                "c784ee9fdab44e1395b8dee7d7a497d5",
                good_schedules=[
                    "standaard",
                ],
            )
        _LOGGER.debug("ERROR raised: %s", exc.value)

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval,
        # set testday to Monday to force an incremental update
        self.smile_setup = "updated/anna_heatpump_heating"
        await self.device_test(
            smile, "2020-04-13 00:00:01", testdata_updated, initialize=False
        )
        assert smile.device_items == 63
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling(self):
        """Test an Anna with Elga setup in cooling mode.

        This test also covers the situation that the operation-mode it switched
        from heating to cooling due to the outdoor temperature rising above the
        cooling_activation_outdoor_temperature threshold.
        """
        testdata = {
            "015ae9ea3f964e668e490fa39da3870b": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 22.0},
            },
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "dev_class": "heater_central",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "model": "Generic heater/cooler",
                "name": "OpenTherm",
                "vendor": "Techneco",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "compressor_state": True,
                    "cooling_enabled": True,
                    "cooling_state": True,
                    "slave_boiler_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 24.7,
                    "domestic_hot_water_setpoint": 60.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 40,
                    "return_temperature": 23.8,
                    "water_pressure": 1.61,
                    "outdoor_air_temperature": 22.0,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "3cb70739631c4d17a86b8b12e8a5161b": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "c784ee9fdab44e1395b8dee7d7a497d5",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 22.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["no_frost", "home", "away", "asleep", "vacation"],
                "active_preset": "home",
                "available_schedules": ["standaard", "off"],
                "select_schedule": "off",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 22.3,
                    "illuminance": 25.5,
                    "cooling_activation_outdoor_temperature": 21.0,
                    "cooling_deactivation_threshold": 6.0,
                    "setpoint_low": 4.0,
                    "setpoint_high": 22.0,
                },
            },
        }

        self.smile_setup = "anna_heatpump_cooling"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-04-19 00:00:01", testdata)
        assert smile._last_active["c784ee9fdab44e1395b8dee7d7a497d5"] == "standaard"
        assert smile.device_items == 63
        assert self.cooling_present
        assert not self.notifications

        assert smile._cooling_enabled
        assert smile._cooling_active

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                smile,
                "c784ee9fdab44e1395b8dee7d7a497d5",
                good_schedules=[
                    "standaard",
                ],
            )
        _LOGGER.debug("ERROR raised: %s", exc.value)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling_fake_firmware(self):
        """Test an Anna with a fake Loria/Thermastate setup in cooling mode.

        The Anna + Elga firmware has been amended with the point_log cooling_enabled and
        gateway/features/cooling keys.
        This test also covers the situation that the operation-mode it switched
        from heating to cooling due to the outdoor temperature rising above the
        cooling_activation_outdoor_temperature threshold.
        """
        testdata = {
            # Heater central
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "binary_sensors": {
                    "cooling_enabled": True,
                    "cooling_state": True,
                    "dhw_state": False,
                    "heating_state": False,
                },
                "sensors": {
                    "modulation_level": 100,
                },
            },
            # Gateway
            "015ae9ea3f964e668e490fa39da3870b": {
                "firmware": "4.10.10",
            },
        }

        self.smile_setup = "anna_heatpump_cooling_fake_firmware"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.10.10"

        await self.device_test(smile, "2020-04-19 00:00:01", testdata)
        assert smile.device_items == 63
        assert smile._cooling_present
        assert smile._cooling_enabled
        assert smile._cooling_active

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2(self):
        """Test a 2nd Anna with Elga setup, cooling off, in idle mode (with missing outdoor temperature - solved)."""
        testdata = {
            "fb49af122f6e4b0f91267e1cf7666d6f": {
                "dev_class": "gateway",
                "firmware": "4.2.1",
                "hardware": "AME Smile 2.0 board",
                "location": "d34dfe6ab90b410c98068e75de3eb631",
                "mac_address": "C4930002FE76",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 13.0},
            },
            "573c152e7d4f4720878222bd75638f5b": {
                "dev_class": "heater_central",
                "location": "d34dfe6ab90b410c98068e75de3eb631",
                "model": "Generic heater/cooler",
                "name": "OpenTherm",
                "vendor": "Techneco",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "compressor_state": False,
                    "cooling_state": False,
                    "cooling_enabled": False,
                    "slave_boiler_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 22.8,
                    "domestic_hot_water_setpoint": 60.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 23.4,
                    "water_pressure": 0.5,
                    "outdoor_air_temperature": 14.0,
                },
                "switches": {"dhw_cm_switch": True},
            },
            "ebd90df1ab334565b5895f37590ccff4": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "d3ce834534114348be628b61b26d9220",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 19.5,
                    "setpoint_high": 30.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "no_frost", "vacation", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Thermostat schedule", "off"],
                "select_schedule": "Thermostat schedule",
                "mode": "auto",
                "sensors": {
                    "temperature": 20.9,
                    "illuminance": 0.5,
                    "cooling_activation_outdoor_temperature": 26.0,
                    "cooling_deactivation_threshold": 3.0,
                    "setpoint_low": 19.5,
                    "setpoint_high": 30.0,
                },
            },
        }

        self.smile_setup = "anna_elga_2"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.2.1"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-03-13 00:00:01", testdata)
        assert (
            smile._last_active["d3ce834534114348be628b61b26d9220"]
            == "Thermostat schedule"
        )
        assert smile.device_items == 62
        assert smile.gateway_id == "fb49af122f6e4b0f91267e1cf7666d6f"
        assert self.cooling_present
        assert not smile._cooling_enabled
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_schedule_off(self):
        """Test Anna with Elga setup, cooling off, in idle mode, modified to schedule off."""
        testdata = {
            "ebd90df1ab334565b5895f37590ccff4": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "d3ce834534114348be628b61b26d9220",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 19.5,
                    "setpoint_high": 30.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "no_frost", "vacation", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Thermostat schedule", "off"],
                "select_schedule": "off",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 20.9,
                    "illuminance": 0.5,
                    "cooling_activation_outdoor_temperature": 26.0,
                    "cooling_deactivation_threshold": 3.0,
                    "setpoint_low": 19.5,
                    "setpoint_high": 30.0,
                },
            }
        }

        self.smile_setup = "anna_elga_2_schedule_off"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        await self.device_test(smile, "2022-03-13 00:00:01", testdata)
        assert (
            smile._last_active["d3ce834534114348be628b61b26d9220"]
            == "Thermostat schedule"
        )
        assert smile._cooling_present
        assert not smile._cooling_enabled
        assert smile.device_items == 62

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_cooling(self):
        """Test a 2nd Anna with Elga setup with cooling active.

        This testcase also covers testing of the generation of a cooling-based
        schedule, opposite the generation of a heating-based schedule.
        """
        testdata = {
            "573c152e7d4f4720878222bd75638f5b": {
                "available": True,
                "binary_sensors": {
                    "compressor_state": True,
                    "cooling_enabled": True,
                    "cooling_state": True,
                    "dhw_state": False,
                    "flame_state": False,
                    "heating_state": False,
                    "slave_boiler_state": False,
                },
                "dev_class": "heater_central",
                "location": "d34dfe6ab90b410c98068e75de3eb631",
                "maximum_boiler_temperature": {
                    "lower_bound": 0.0,
                    "resolution": 1.0,
                    "setpoint": 60.0,
                    "upper_bound": 100.0,
                },
                "model": "Generic heater/cooler",
                "name": "OpenTherm",
                "sensors": {
                    "domestic_hot_water_setpoint": 60.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "outdoor_air_temperature": 30.0,
                    "return_temperature": 23.4,
                    "water_pressure": 0.5,
                    "water_temperature": 22.8,
                },
                "switches": {"dhw_cm_switch": True},
                "vendor": "Techneco",
            },
            "ebd90df1ab334565b5895f37590ccff4": {
                "active_preset": "home",
                "available_schedules": ["Thermostat schedule", "off"],
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "d3ce834534114348be628b61b26d9220",
                "mode": "auto",
                "model": "ThermoTouch",
                "name": "Anna",
                "preset_modes": ["away", "no_frost", "vacation", "home", "asleep"],
                "select_schedule": "Thermostat schedule",
                "sensors": {
                    "cooling_activation_outdoor_temperature": 26.0,
                    "cooling_deactivation_threshold": 3.0,
                    "illuminance": 0.5,
                    "setpoint_high": 23.0,
                    "setpoint_low": 4.0,
                    "temperature": 24.9,
                },
                "thermostat": {
                    "lower_bound": 4.0,
                    "resolution": 0.1,
                    "setpoint_high": 23.0,
                    "setpoint_low": 4.0,
                    "upper_bound": 30.0,
                },
                "vendor": "Plugwise",
            },
            "fb49af122f6e4b0f91267e1cf7666d6f": {
                "binary_sensors": {"plugwise_notification": False},
                "dev_class": "gateway",
                "firmware": "4.2.1",
                "hardware": "AME Smile 2.0 board",
                "location": "d34dfe6ab90b410c98068e75de3eb631",
                "mac_address": "C4930002FE76",
                "model": "Gateway",
                "name": "Smile Anna",
                "sensors": {"outdoor_temperature": 31.0},
                "vendor": "Plugwise",
            },
        }

        self.smile_setup = "anna_elga_2_cooling"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.2.1"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-03-10 00:00:01", testdata)
        assert (
            smile._last_active["d3ce834534114348be628b61b26d9220"]
            == "Thermostat schedule"
        )
        assert smile.device_items == 62
        assert not self.notifications

        assert self.cooling_present
        assert smile._cooling_enabled
        assert smile._cooling_active

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_heating_idle(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        testdata = {
            "582dfbdace4d4aeb832923ce7d1ddda0": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "15da035090b847e7a21f93e08c015ebc",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 20.5,
                    "setpoint_high": 30.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "vacation", "no_frost", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Winter", "Test ", "off"],
                "select_schedule": "Winter",
                "mode": "auto",
                "sensors": {
                    "temperature": 22.1,
                    "illuminance": 45.0,
                    "setpoint_low": 20.5,
                    "setpoint_high": 30.0,
                },
            },
            "bfb5ee0a88e14e5f97bfa725a760cc49": {
                "dev_class": "heater_central",
                "location": "674b657c138a41a291d315d7471deb06",
                "model": "173",
                "name": "OpenTherm",
                "vendor": "Atlantic",
                "select_dhw_mode": "auto",
                "maximum_boiler_temperature": {
                    "setpoint": 40.0,
                    "lower_bound": 25.0,
                    "upper_bound": 45.0,
                    "resolution": 0.01,
                },
                "max_dhw_temperature": {
                    "setpoint": 53.0,
                    "lower_bound": 35.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "dhw_modes": ["off", "auto", "boost", "eco", "comfort"],
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "cooling_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 25.3,
                    "dhw_temperature": 52.9,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 26.3,
                    "outdoor_air_temperature": 17.3,
                },
                "switches": {"dhw_cm_switch": True, "cooling_ena_switch": False},
            },
            "9ff0569b4984459fb243af64c0901894": {
                "dev_class": "gateway",
                "firmware": "4.3.8",
                "hardware": "AME Smile 2.0 board",
                "location": "674b657c138a41a291d315d7471deb06",
                "mac_address": "C493000278E2",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 15.5},
            },
        }

        self.smile_setup = "anna_loria_heating_idle"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile._last_active["15da035090b847e7a21f93e08c015ebc"] == "Winter"
        assert smile.device_items == 63
        assert smile._cooling_present
        assert not smile._cooling_enabled

        switch_change = await self.tinker_switch(
            smile,
            "bfb5ee0a88e14e5f97bfa725a760cc49",
            model="cooling_ena_switch",
        )
        assert switch_change

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                smile,
                "15da035090b847e7a21f93e08c015ebc",
                good_schedules=[
                    "Winter",
                ],
            )
        _LOGGER.debug("ERROR raised: %s", exc.value)

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat_temp(
                smile,
                "15da035090b847e7a21f93e08c015ebc",
                block_cooling=True,
            )
        _LOGGER.debug("ERROR raised: %s", exc.value)

        await self.tinker_dhw_mode(smile)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_cooling_active(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        testdata = {
            "582dfbdace4d4aeb832923ce7d1ddda0": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "15da035090b847e7a21f93e08c015ebc",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 23.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "vacation", "no_frost", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Winter", "Test ", "off"],
                "select_schedule": "Winter",
                "mode": "auto",
                "sensors": {
                    "temperature": 24.1,
                    "illuminance": 45.0,
                    "setpoint_low": 4.0,
                    "setpoint_high": 23.5,
                },
            },
            "bfb5ee0a88e14e5f97bfa725a760cc49": {
                "dev_class": "heater_central",
                "location": "674b657c138a41a291d315d7471deb06",
                "model": "173",
                "name": "OpenTherm",
                "vendor": "Atlantic",
                "select_dhw_mode": "auto",
                "maximum_boiler_temperature": {
                    "setpoint": 40.0,
                    "lower_bound": 25.0,
                    "upper_bound": 45.0,
                    "resolution": 0.01,
                },
                "max_dhw_temperature": {
                    "setpoint": 53.0,
                    "lower_bound": 35.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "dhw_modes": ["off", "auto", "boost", "eco", "comfort"],
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "cooling_state": True,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 25.3,
                    "dhw_temperature": 52.9,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 100,
                    "return_temperature": 26.3,
                    "outdoor_air_temperature": 17.3,
                },
                "switches": {"dhw_cm_switch": True, "cooling_ena_switch": True},
            },
            "9ff0569b4984459fb243af64c0901894": {
                "dev_class": "gateway",
                "firmware": "4.3.8",
                "hardware": "AME Smile 2.0 board",
                "location": "674b657c138a41a291d315d7471deb06",
                "mac_address": "C493000278E2",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 15.5},
            },
        }

        self.smile_setup = "anna_loria_cooling_active"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile._last_active["15da035090b847e7a21f93e08c015ebc"] == "Winter"
        assert smile.device_items == 63
        assert smile._cooling_present
        assert smile._cooling_enabled

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_driessens(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        testdata = {
            "5c118b1842e943c0a5b6ef88a60bb17a": {
                "binary_sensors": {"plugwise_notification": False},
                "dev_class": "gateway",
                "firmware": "4.4.1",
                "hardware": "AME Smile 2.0 board",
                "location": "82c15f65c9bf44c592d69e16139355e3",
                "mac_address": "D40FB2011556",
                "model": "Gateway",
                "name": "Smile Anna",
                "sensors": {"outdoor_temperature": 6.81},
                "vendor": "Plugwise",
            },
            "9fb768d699e44c7fb5cc50309dc4e7d4": {
                "active_preset": "home",
                "available_schedules": [
                    "Verwarmen@9-23u",
                    "VAKANTIE (winter)",
                    "VERWARMEN",
                    "KOELEN",
                    "off",
                ],
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "fa70e08550c94de3a34feb27ecf31421",
                "mode": "auto",
                "model": "ThermoTouch",
                "name": "Anna",
                "preset_modes": ["no_frost", "asleep", "vacation", "away", "home"],
                "select_schedule": "Verwarmen@9-23u",
                "sensors": {
                    "illuminance": 5.5,
                    "setpoint_high": 30.0,
                    "setpoint_low": 20.0,
                    "temperature": 21.2,
                },
                "temperature_offset": {
                    "lower_bound": -2.0,
                    "resolution": 0.1,
                    "setpoint": 0.0,
                    "upper_bound": 2.0,
                },
                "thermostat": {
                    "lower_bound": 4.0,
                    "resolution": 0.1,
                    "setpoint_high": 30.0,
                    "setpoint_low": 20.0,
                    "upper_bound": 30.0,
                },
                "vendor": "Plugwise",
            },
            "a449cbc334ae4a5bb7f89064984b2906": {
                "available": True,
                "binary_sensors": {
                    "cooling_state": False,
                    "dhw_state": False,
                    "flame_state": False,
                    "heating_state": False,
                },
                "dev_class": "heater_central",
                "dhw_modes": ["comfort", "eco", "off", "boost", "auto"],
                "location": "82c15f65c9bf44c592d69e16139355e3",
                "max_dhw_temperature": {
                    "lower_bound": 35.0,
                    "resolution": 0.01,
                    "setpoint": 53.0,
                    "upper_bound": 60.0,
                },
                "maximum_boiler_temperature": {
                    "lower_bound": 25.0,
                    "resolution": 0.01,
                    "setpoint": 45.0,
                    "upper_bound": 45.0,
                },
                "model": "173",
                "name": "OpenTherm",
                "select_dhw_mode": "auto",
                "sensors": {
                    "dhw_temperature": 49.5,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "outdoor_air_temperature": 7.63,
                    "return_temperature": 23.0,
                    "water_temperature": 23.3,
                },
                "switches": {"cooling_ena_switch": False, "dhw_cm_switch": True},
                "vendor": "Atlantic",
            },
        }
        self.smile_setup = "anna_loria_driessens"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.device_items == 63
        assert smile._cooling_present
        assert not smile._cooling_enabled

        await smile.close_connection()
        await self.disconnect(server, client)
