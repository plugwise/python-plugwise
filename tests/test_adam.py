"""Test Plugwise module Adam related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise, pw_exceptions


class TestPlugwiseAdam(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for Adam standalone, i.e. not combined with Anna or Jip."""

    @pytest.mark.asyncio
    async def test_connect_adam_zone_per_device(self):
        """Test an extensive setup of Adam with a zone per device."""
        testdata = {
            "df4a4a8169904cdb9c03d61a21f42140": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Lisa",
                "name": "Zone Lisa Bios",
                "zigbee_mac_address": "ABCD012345670A06",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "off",
                "mode": "heat",
                "sensors": {"temperature": 16.5, "setpoint": 13.0, "battery": 67},
            },
            "b310b72a0e354bfab43089919b9a88bf": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Tom/Floor",
                "name": "Floor kraan",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 26.2,
                    "setpoint": 21.5,
                    "temperature_difference": 3.7,
                    "valve_position": 0.0,
                },
            },
            "a2c3583e0a6349358998b760cea82d2a": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Tom/Floor",
                "name": "Bios Cv Thermostatic Radiator ",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 17.1,
                    "setpoint": 13.0,
                    "battery": 62,
                    "temperature_difference": -0.1,
                    "valve_position": 0.0,
                },
            },
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-08-02T02:00:00+02:00",
                "hardware": "255",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Lisa",
                "name": "Zone Lisa WK",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 21.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "GF7  Woonkamer",
                "mode": "auto",
                "sensors": {"temperature": 21.1, "setpoint": 21.5, "battery": 34},
            },
            "fe799307f1624099878210aa0b9f1475": {
                "dev_class": "gateway",
                "firmware": "3.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "select_regulation_mode": "heating",
                "binary_sensors": {"plugwise_notification": True},
                "sensors": {"outdoor_temperature": 7.69},
            },
            "d3da73bde12a47d5a6b8f9dad971f2ec": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Jessie",
                "zigbee_mac_address": "ABCD012345670A10",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 16.9,
                    "setpoint": 16.0,
                    "battery": 62,
                    "temperature_difference": 0.1,
                    "valve_position": 0.0,
                },
            },
            "21f2b542c49845e6bb416884c55778d6": {
                "dev_class": "game_console",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "4efbab4c8bb84fbab26c8decf670eb96",
                "model": "Plug",
                "name": "Playstation Smart Plug",
                "zigbee_mac_address": "ABCD012345670A12",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 81.2,
                    "electricity_consumed_interval": 12.7,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "78d1126fc4c743db81b61c20e88342a7": {
                "dev_class": "central_heating_pump",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Plug",
                "name": "CV Pomp",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 35.8,
                    "electricity_consumed_interval": 5.85,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "90986d591dcd426cae3ec3e8111ff730": {
                "dev_class": "heater_central",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "model": "Unknown",
                "name": "OnOff",
                "binary_sensors": {"heating_state": False},
                "sensors": {
                    "water_temperature": 70.0,
                    "intended_boiler_temperature": 70.0,
                    "modulation_level": 1,
                },
            },
            "cd0ddb54ef694e11ac18ed1cbce5dbbd": {
                "dev_class": "vcr",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "e704bae65654496f9cade9c855decdfe",
                "model": "Plug",
                "name": "NAS",
                "zigbee_mac_address": "ABCD012345670A14",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 16.5,
                    "electricity_consumed_interval": 0.29,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "4a810418d5394b3f82727340b91ba740": {
                "dev_class": "router",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "0217e9743c174eef9d6e9f680d403ce2",
                "model": "Plug",
                "name": "USG Smart Plug",
                "zigbee_mac_address": "ABCD012345670A16",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 8.5,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "02cf28bfec924855854c544690a609ef": {
                "dev_class": "vcr",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "c4d2bda6df8146caa2e5c2b5dc65660e",
                "model": "Plug",
                "name": "NVR",
                "zigbee_mac_address": "ABCD012345670A15",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 34.0,
                    "electricity_consumed_interval": 8.65,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "a28f588dc4a049a483fd03a30361ad3a": {
                "dev_class": "settop",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Fibaro HC2",
                "zigbee_mac_address": "ABCD012345670A13",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.5,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "6a3bf693d05e48e0b460c815a4fdd09d": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Lisa",
                "name": "Zone Thermostat Jessie",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 16.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "asleep",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "CV Jessie",
                "mode": "auto",
                "sensors": {"temperature": 17.1, "setpoint": 16.0, "battery": 37},
            },
            "680423ff840043738f42cc7f1ff97a36": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Badkamer",
                "zigbee_mac_address": "ABCD012345670A17",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 19.1,
                    "setpoint": 14.0,
                    "battery": 51,
                    "temperature_difference": -0.3,
                    "valve_position": 0.0,
                },
            },
            "f1fee6043d3642a9b0a65297455f008e": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Lisa",
                "name": "Zone Thermostat Badkamer",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 14.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "Badkamer Schema",
                "mode": "auto",
                "sensors": {"temperature": 18.8, "setpoint": 14.0, "battery": 92},
            },
            "675416a629f343c495449970e2ca37b5": {
                "dev_class": "router",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "2b1591ecf6344d4d93b03dece9747648",
                "model": "Plug",
                "name": "Ziggo Modem",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.2,
                    "electricity_consumed_interval": 2.8,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "e7693eb9582644e5b865dba8d4447cf1": {
                "dev_class": "thermostatic_radiator_valve",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "446ac08dd04d4eff8ac57489757b7314",
                "model": "Tom/Floor",
                "name": "CV Kraan Garage",
                "zigbee_mac_address": "ABCD012345670A11",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 5.5,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "no_frost",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "off",
                "mode": "heat",
                "sensors": {
                    "temperature": 15.6,
                    "setpoint": 5.5,
                    "battery": 68,
                    "temperature_difference": 0.1,
                    "valve_position": 0.0,
                },
            },
        }

        self.smile_setup = "adam_zone_per_device"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.15"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "fe799307f1624099878210aa0b9f1475"
        assert (
            smile._last_active["12493538af164a409c6a1c79e38afe1c"] == "Badkamer Schema"
        )
        assert (
            smile._last_active["c50f167537524366a5af7aa3942feb1e"] == "GF7  Woonkamer"
        )
        assert smile._last_active["82fa13f017d240daa0d0ea1775420f24"] == "CV Jessie"
        assert (
            smile._last_active["08963fec7c53423ca5680aa4cb502c63"] == "Badkamer Schema"
        )
        assert (
            smile._last_active["446ac08dd04d4eff8ac57489757b7314"] == "Badkamer Schema"
        )
        assert smile.device_items == 315

        assert "af82e4ccf9c548528166d38e560662a4" in self.notifications
        await smile.delete_notification()

        result = await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schedules=["GF7  Woonkamer"]
        )
        assert result
        result = await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schedules=["CV Jessie"]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "675416a629f343c495449970e2ca37b5"
        )
        assert not switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        result = await self.tinker_thermostat(
            smile,
            "c50f167537524366a5af7aa3942feb1e",
            good_schedules=["GF7  Woonkamer"],
            unhappy=True,
        )
        assert result
        result = await self.tinker_thermostat(
            smile,
            "82fa13f017d240daa0d0ea1775420f24",
            good_schedules=["CV Jessie"],
            unhappy=True,
        )
        assert result

        try:
            await smile.delete_notification()
            assert False  # pragma: no cover
        except pw_exceptions.ResponseError:
            assert True

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_multiple_devices_per_zone(self):
        """Test an extensive setup of Adam with multiple devices per zone."""
        testdata = {
            "df4a4a8169904cdb9c03d61a21f42140": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Lisa",
                "name": "Zone Lisa Bios",
                "zigbee_mac_address": "ABCD012345670A06",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "off",
                "mode": "heat",
                "sensors": {"temperature": 16.5, "setpoint": 13.0, "battery": 67},
            },
            "b310b72a0e354bfab43089919b9a88bf": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Tom/Floor",
                "name": "Floor kraan",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 26.0,
                    "setpoint": 21.5,
                    "temperature_difference": 3.5,
                    "valve_position": 100,
                },
            },
            "a2c3583e0a6349358998b760cea82d2a": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Tom/Floor",
                "name": "Bios Cv Thermostatic Radiator ",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 17.2,
                    "setpoint": 13.0,
                    "battery": 62,
                    "temperature_difference": -0.2,
                    "valve_position": 0.0,
                },
            },
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-08-02T02:00:00+02:00",
                "hardware": "255",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Lisa",
                "name": "Zone Lisa WK",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 21.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "GF7  Woonkamer",
                "mode": "auto",
                "sensors": {"temperature": 20.9, "setpoint": 21.5, "battery": 34},
            },
            "fe799307f1624099878210aa0b9f1475": {
                "dev_class": "gateway",
                "firmware": "3.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "select_regulation_mode": "heating",
                "binary_sensors": {"plugwise_notification": True},
                "sensors": {"outdoor_temperature": 7.81},
            },
            "d3da73bde12a47d5a6b8f9dad971f2ec": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Jessie",
                "zigbee_mac_address": "ABCD012345670A10",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 17.1,
                    "setpoint": 15.0,
                    "battery": 62,
                    "temperature_difference": 0.1,
                    "valve_position": 0.0,
                },
            },
            "21f2b542c49845e6bb416884c55778d6": {
                "dev_class": "game_console",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Playstation Smart Plug",
                "zigbee_mac_address": "ABCD012345670A12",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 82.6,
                    "electricity_consumed_interval": 8.6,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "78d1126fc4c743db81b61c20e88342a7": {
                "dev_class": "central_heating_pump",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Plug",
                "name": "CV Pomp",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 35.6,
                    "electricity_consumed_interval": 7.37,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "90986d591dcd426cae3ec3e8111ff730": {
                "dev_class": "heater_central",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "model": "Unknown",
                "name": "OnOff",
                "binary_sensors": {"heating_state": True},
                "sensors": {
                    "water_temperature": 70.0,
                    "intended_boiler_temperature": 70.0,
                    "modulation_level": 1,
                },
            },
            "cd0ddb54ef694e11ac18ed1cbce5dbbd": {
                "dev_class": "vcr",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "NAS",
                "zigbee_mac_address": "ABCD012345670A14",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 16.5,
                    "electricity_consumed_interval": 0.5,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "4a810418d5394b3f82727340b91ba740": {
                "dev_class": "router",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "USG Smart Plug",
                "zigbee_mac_address": "ABCD012345670A16",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 8.5,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "02cf28bfec924855854c544690a609ef": {
                "dev_class": "vcr",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "NVR",
                "zigbee_mac_address": "ABCD012345670A15",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 34.0,
                    "electricity_consumed_interval": 9.15,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "a28f588dc4a049a483fd03a30361ad3a": {
                "dev_class": "settop",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Fibaro HC2",
                "zigbee_mac_address": "ABCD012345670A13",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.5,
                    "electricity_consumed_interval": 3.8,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "6a3bf693d05e48e0b460c815a4fdd09d": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Lisa",
                "name": "Zone Thermostat Jessie",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 15.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "asleep",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "CV Jessie",
                "mode": "auto",
                "sensors": {"temperature": 17.2, "setpoint": 15.0, "battery": 37},
            },
            "680423ff840043738f42cc7f1ff97a36": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Badkamer",
                "zigbee_mac_address": "ABCD012345670A17",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 19.1,
                    "setpoint": 14.0,
                    "battery": 51,
                    "temperature_difference": -0.4,
                    "valve_position": 0.0,
                },
            },
            "f1fee6043d3642a9b0a65297455f008e": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Lisa",
                "name": "Zone Thermostat Badkamer",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 14.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "Badkamer Schema",
                "mode": "auto",
                "sensors": {"temperature": 18.9, "setpoint": 14.0, "battery": 92},
            },
            "675416a629f343c495449970e2ca37b5": {
                "dev_class": "router",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Ziggo Modem",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.2,
                    "electricity_consumed_interval": 2.97,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "e7693eb9582644e5b865dba8d4447cf1": {
                "dev_class": "thermostatic_radiator_valve",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "446ac08dd04d4eff8ac57489757b7314",
                "model": "Tom/Floor",
                "name": "CV Kraan Garage",
                "zigbee_mac_address": "ABCD012345670A11",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 5.5,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "no_frost",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                    "off",
                ],
                "select_schedule": "off",
                "mode": "heat",
                "sensors": {
                    "temperature": 15.6,
                    "setpoint": 5.5,
                    "battery": 68,
                    "temperature_difference": 0.0,
                    "valve_position": 0.0,
                },
            },
        }

        self.smile_setup = "adam_multiple_devices_per_zone"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.15"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert (
            smile._last_active["12493538af164a409c6a1c79e38afe1c"] == "Badkamer Schema"
        )
        assert (
            smile._last_active["c50f167537524366a5af7aa3942feb1e"] == "GF7  Woonkamer"
        )
        assert smile._last_active["82fa13f017d240daa0d0ea1775420f24"] == "CV Jessie"
        assert (
            smile._last_active["08963fec7c53423ca5680aa4cb502c63"] == "Badkamer Schema"
        )
        assert (
            smile._last_active["446ac08dd04d4eff8ac57489757b7314"] == "Badkamer Schema"
        )
        assert smile.device_items == 315

        assert "af82e4ccf9c548528166d38e560662a4" in self.notifications

        result = await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schedules=["GF7  Woonkamer"]
        )
        assert result
        result = await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schedules=["CV Jessie"]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "675416a629f343c495449970e2ca37b5"
        )
        assert not switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_heatpump_cooling(self):
        """Test Adam with heatpump in cooling mode and idle."""
        testdata = {
            "0ca13e8176204ca7bf6f09de59f81c83": {
                "available": True,
                "binary_sensors": {
                    "cooling_state": False,
                    "dhw_state": False,
                    "flame_state": False,
                    "heating_state": False,
                },
                "dev_class": "heater_central",
                "location": "eedadcb297564f1483faa509179aebed",
                "max_dhw_temperature": {
                    "lower_bound": 40.0,
                    "resolution": 0.01,
                    "setpoint": 60.0,
                    "upper_bound": 65.0,
                },
                "maximum_boiler_temperature": {
                    "lower_bound": 7.0,
                    "resolution": 0.01,
                    "setpoint": 35.0,
                    "upper_bound": 50.0,
                },
                "model": "17.1",
                "name": "OpenTherm",
                "sensors": {
                    "dhw_temperature": 63.5,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "outdoor_air_temperature": 13.5,
                    "return_temperature": 24.9,
                    "water_pressure": 2.0,
                    "water_temperature": 24.5,
                },
                "switches": {"dhw_cm_switch": True},
                "vendor": "Remeha B.V.",
            },
            "1053c8bbf8be43c6921742b146a625f1": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "b52908550469425b812c87f766fe5303",
                "mode": "cool",
                "model": "Lisa",
                "name": "Thermostaat BK",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "off",
                "sensors": {
                    "battery": 55,
                    "setpoint": 18.0,
                    "temperature": 18.8,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 18.0,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A17",
            },
            "1a27dd03b5454c4e8b9e75c8d1afc7af": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "20e735858f8146cead98b873177a4f99",
                "model": "Plug",
                "name": "Smart Plug DB",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A05",
            },
            "2e0fc4db2a6d4cbeb7cf786143543961": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "a562019b0b1f47a4bde8ebe3dbe3e8a9",
                "model": "Plug",
                "name": "Smart Plug KK",
                "sensors": {
                    "electricity_consumed": 2.13,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A06",
            },
            "3b4d2574e2c9443a832b48d19a1c4f06": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "04b15f6e884448288f811d29fb7b1b30",
                "model": "Plug",
                "name": "Smart Plug SJ",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A14",
            },
            "3f0afa71f16c45ab964050002560e43c": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "fa5fa6b34f6b40a0972988b20e888ed4",
                "model": "Plug",
                "name": "Smart Plug WK",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A18",
            },
            "47e2c550a33846b680725aa3fb229473": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "20e735858f8146cead98b873177a4f99",
                "mode": "cool",
                "model": "Lisa",
                "name": "Thermostaat DB",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "off",
                "sensors": {
                    "setpoint": 18.0,
                    "temperature": 22.0,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 18.0,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A20",
            },
            "5ead63c65e5f44e7870ba2bd680ceb9e": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "9a27714b970547ee9a6bdadc2b815ad5",
                "model": "Plug",
                "name": "Smart Plug SQ",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A15",
            },
            "7d97fc3117784cfdafe347bcedcbbbcb": {
                "binary_sensors": {"plugwise_notification": False},
                "dev_class": "gateway",
                "firmware": "3.2.8",
                "hardware": "AME Smile 2.0 board",
                "location": "eedadcb297564f1483faa509179aebed",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "select_regulation_mode": "cooling",
                "regulation_modes": [
                    "heating",
                    "off",
                    "bleeding_cold",
                    "bleeding_hot",
                    "cooling",
                ],
                "sensors": {"outdoor_temperature": 13.4},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670101",
            },
            "7fda9f84f01342f8afe9ebbbbff30c0f": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "e39529c79ab54fda9bed26cfc0447546",
                "mode": "cool",
                "model": "Lisa",
                "name": "Thermostaat JM",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "off",
                "sensors": {
                    "setpoint": 18.0,
                    "temperature": 20.0,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 18.0,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A01",
            },
            "838c2f48195242709b87217cf8d8a71f": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "b52908550469425b812c87f766fe5303",
                "model": "Plug",
                "name": "Smart Plug BK",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A12",
            },
            "8a482fa9dddb43acb765d019d8c9838b": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "5cc21042f87f4b4c94ccb5537c47a53f",
                "model": "Plug",
                "name": "Smart Plug BK2",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A10",
            },
            "96714ad90fc948bcbcb5021c4b9f5ae9": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "e39529c79ab54fda9bed26cfc0447546",
                "model": "Plug",
                "name": "Smart Plug JM",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A03",
            },
            "a03b6e8e76dd4646af1a77c31dd9370c": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "93ac3f7bf25342f58cbb77c4a99ac0b3",
                "model": "Plug",
                "name": "Smart Plug RB",
                "sensors": {
                    "electricity_consumed": 3.13,
                    "electricity_consumed_interval": 0.77,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A08",
            },
            "bbcffa48019f4b09b8368bbaf9559e68": {
                "available": True,
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "8cf650a4c10c44819e426bed406aec34",
                "model": "Plug",
                "name": "Smart Plug BK1",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A16",
            },
            "beb32da072274e698146db8b022f3c36": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "9a27714b970547ee9a6bdadc2b815ad5",
                "mode": "cool",
                "model": "Lisa",
                "name": "Thermostaat SQ",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "off",
                "sensors": {
                    "setpoint": 18.5,
                    "temperature": 21.4,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 18.5,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A07",
            },
            "c4ed311d54e341f58b4cdd201d1fde7e": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "93ac3f7bf25342f58cbb77c4a99ac0b3",
                "mode": "cool",
                "model": "Lisa",
                "name": "Thermostaat RB",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "off",
                "sensors": {
                    "setpoint": 17.0,
                    "temperature": 20.7,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 17.0,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A04",
            },
            "ca79d23ae0094120b877558734cff85c": {
                "active_preset": "away",
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "thermostat",
                "location": "fa5fa6b34f6b40a0972988b20e888ed4",
                "mode": "auto",
                "model": "ThermoTouch",
                "name": "Thermostaat WK",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "Werkdag schema",
                "sensors": {
                    "setpoint": 21.5,
                    "temperature": 22.5,
                },
                "thermostat": {
                    "lower_bound": 1.0,
                    "resolution": 0.01,
                    "setpoint": 21.5,
                    "upper_bound": 35.0,
                },
                "vendor": "Plugwise",
            },
            "d3a276aeb3114a509bab1e4bf8c40348": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "04b15f6e884448288f811d29fb7b1b30",
                "mode": "cool",
                "model": "Lisa",
                "name": "Thermostaat SJ",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "off",
                "sensors": {
                    "setpoint": 20.5,
                    "temperature": 22.6,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 20.5,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A13",
            },
            "ea8372c0e3ad4622ad45a041d02425f5": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "a562019b0b1f47a4bde8ebe3dbe3e8a9",
                "mode": "auto",
                "model": "Lisa",
                "name": "Thermostaat KK",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "Werkdag schema",
                "sensors": {
                    "battery": 53,
                    "setpoint": 21.5,
                    "temperature": 22.5,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 21.5,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A02",
            },
            "eac5db95d97241f6b17790897847ccf5": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "8cf650a4c10c44819e426bed406aec34",
                "mode": "auto",
                "model": "Lisa",
                "name": "Thermostaat BK1",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "Werkdag schema",
                "sensors": {
                    "setpoint": 20.5,
                    "temperature": 21.5,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 20.5,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A09",
            },
            "f04c985c11ad4848b8fcd710343f9dcf": {
                "active_preset": "away",
                "available": True,
                "available_schedules": [
                    "Opstaan weekdag",
                    "Werkdag schema",
                    "Weekend",
                    "off",
                ],
                "control_state": "off",
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "5cc21042f87f4b4c94ccb5537c47a53f",
                "mode": "auto",
                "model": "Lisa",
                "name": "Thermostaat  BK2",
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "select_schedule": "Werkdag schema",
                "sensors": {
                    "setpoint": 20.5,
                    "temperature": 21.9,
                },
                "thermostat": {
                    "lower_bound": 0.0,
                    "resolution": 0.01,
                    "setpoint": 20.5,
                    "upper_bound": 99.9,
                },
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A11",
            },
        }

        self.smile_setup = "adam_heatpump_cooling"
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, "2022-01-02 00:00:01", testdata)
        assert (
            smile._last_active["b52908550469425b812c87f766fe5303"] == "Werkdag schema"
        )
        assert (
            smile._last_active["20e735858f8146cead98b873177a4f99"] == "Werkdag schema"
        )
        assert (
            smile._last_active["e39529c79ab54fda9bed26cfc0447546"] == "Werkdag schema"
        )
        assert (
            smile._last_active["9a27714b970547ee9a6bdadc2b815ad5"] == "Werkdag schema"
        )
        assert (
            smile._last_active["93ac3f7bf25342f58cbb77c4a99ac0b3"] == "Werkdag schema"
        )
        assert (
            smile._last_active["fa5fa6b34f6b40a0972988b20e888ed4"] == "Werkdag schema"
        )
        assert (
            smile._last_active["04b15f6e884448288f811d29fb7b1b30"] == "Werkdag schema"
        )
        assert (
            smile._last_active["a562019b0b1f47a4bde8ebe3dbe3e8a9"] == "Werkdag schema"
        )
        assert (
            smile._last_active["8cf650a4c10c44819e426bed406aec34"] == "Werkdag schema"
        )
        assert (
            smile._last_active["5cc21042f87f4b4c94ccb5537c47a53f"] == "Werkdag schema"
        )
        assert smile.device_items == 413

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_onoff_cooling_fake_firmware(self):
        """Test an Adam with a fake OnOff cooling device in cooling mode."""
        testdata = {
            # Heater central
            "0ca13e8176204ca7bf6f09de59f81c83": {
                "binary_sensors": {
                    "cooling_state": True,
                    "dhw_state": False,
                    "heating_state": False,
                },
                "sensors": {
                    "modulation_level": 0,
                },
            },
        }

        self.smile_setup = "adam_onoff_cooling_fake_firmware"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"

        await self.device_test(smile, "2022-01-02 00:00:01", testdata)
        assert smile.device_items == 54
        assert smile._cooling_present
        assert smile._cooling_enabled

        await smile.close_connection()
        await self.disconnect(server, client)
