"""Test Plugwise module Stretch related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise


class TestPlugwiseStretch(
    TestPlugwise
):  # pylint: disable=attribute-defined-outside-init
    """Tests for Stretch."""

    @pytest.mark.asyncio
    async def test_connect_stretch_v31(self):
        """Test a legacy Stretch with firmware 3.1 setup."""
        testdata = {
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "dev_class": "gateway",
                "firmware": "3.1.11",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "mac_address": "01:23:45:67:89:AB",
                "model": "Gateway",
                "name": "Stretch",
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670101",
            },
            "5871317346d045bc9f6b987ef25ee638": {
                "dev_class": "water_heater_vessel",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4028",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Boiler (1EB31)",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 1.19,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "e1c884e7dede431dadee09506ec4f859": {
                "dev_class": "refrigerator",
                "firmware": "2011-06-27T10:47:37+02:00",
                "hardware": "6539-0700-7330",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle+ type F",
                "name": "Koelkast (92C4A)",
                "zigbee_mac_address": "0123456789AB",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 50.5,
                    "electricity_consumed_interval": 0.08,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "aac7b735042c4832ac9ff33aae4f453b": {
                "dev_class": "dishwasher",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4022",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Vaatwasser (2a1ab)",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.71,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "cfe95cf3de1948c0b8955125bf754614": {
                "dev_class": "dryer",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Droger (52559)",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "059e4d03c7a34d278add5c7a4a781d19": {
                "dev_class": "washingmachine",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Wasmachine (52AC1)",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "d950b314e9d8499f968e6db8d82ef78c": {
                "dev_class": "report",
                "model": "Switchgroup",
                "name": "Stroomvreters",
                "members": [
                    "059e4d03c7a34d278add5c7a4a781d19",
                    "5871317346d045bc9f6b987ef25ee638",
                    "aac7b735042c4832ac9ff33aae4f453b",
                    "cfe95cf3de1948c0b8955125bf754614",
                    "e1c884e7dede431dadee09506ec4f859",
                ],
                "switches": {"relay": True},
            },
            "d03738edfcc947f7b8f4573571d90d2d": {
                "dev_class": "switching",
                "model": "Switchgroup",
                "name": "Schakel",
                "members": [
                    "059e4d03c7a34d278add5c7a4a781d19",
                    "cfe95cf3de1948c0b8955125bf754614",
                ],
                "switches": {"relay": True},
            },
        }
        testdata_updated = {
            "aac7b735042c4832ac9ff33aae4f453b": {
                "sensors": {
                    "electricity_consumed": 1000.0,
                    "electricity_consumed_interval": 20.7,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "cfe95cf3de1948c0b8955125bf754614": {
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "059e4d03c7a34d278add5c7a4a781d19": {
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "d03738edfcc947f7b8f4573571d90d2d": {
                "members": [
                    "059e4d03c7a34d278add5c7a4a781d19",
                    "cfe95cf3de1948c0b8955125bf754614",
                ],
                "switches": {"relay": False},
            },
        }

        self.smile_setup = "stretch_v31"
        server, smile, client = await self.connect_wrapper(stretch=True)
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.1.11"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "0000aaaa0000aaaa0000aaaa0000aa00"
        assert smile.device_items == 83

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        self.smile_setup = "updated/stretch_v31"
        await self.device_test(
            smile, "2022-05-16 00:00:01", testdata_updated, initialize=False
        )

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v23(self):
        """Test a legacy Stretch with firmware 2.3 setup."""
        testdata = {
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "dev_class": "gateway",
                "firmware": "2.3.12",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "mac_address": "01:23:45:67:89:AB",
                "model": "Gateway",
                "name": "Stretch",
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670101",
            },
            "09c8ce93d7064fa6a233c0e4c2449bfe": {
                "dev_class": "lamp",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "kerstboom buiten 043B016",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "33a1c784a9ff4c2d8766a0212714be09": {
                "dev_class": "lighting",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Barverlichting",
                "zigbee_mac_address": "ABCD012345670A13",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "199fd4b2caa44197aaf5b3128f6464ed": {
                "dev_class": "airconditioner",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Airco 25F69E3",
                "zigbee_mac_address": "ABCD012345670A10",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 2.06,
                    "electricity_consumed_interval": 1.62,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "713427748874454ca1eb4488d7919cf2": {
                "dev_class": "freezer",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Leeg 043220D",
                "zigbee_mac_address": "ABCD012345670A12",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "fd1b74f59e234a9dae4e23b2b5cf07ed": {
                "dev_class": "dryer",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Wasdroger 043AECA",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 1.31,
                    "electricity_consumed_interval": 0.21,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "c71f1cb2100b42ca942f056dcb7eb01f": {
                "dev_class": "tv",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Tv hoek 25F6790",
                "zigbee_mac_address": "ABCD012345670A11",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 33.3,
                    "electricity_consumed_interval": 4.93,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "2cc9a0fe70ef4441a9e4f55dfd64b776": {
                "dev_class": "lamp",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Lamp TV 025F698F",
                "zigbee_mac_address": "ABCD012345670A15",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 4.0,
                    "electricity_consumed_interval": 0.58,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "6518f3f72a82486c97b91e26f2e9bd1d": {
                "dev_class": "charger",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Bed 025F6768",
                "zigbee_mac_address": "ABCD012345670A14",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "828f6ce1e36744689baacdd6ddb1d12c": {
                "dev_class": "washingmachine",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Wasmachine 043AEC7",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 3.5,
                    "electricity_consumed_interval": 0.5,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "71e3e65ffc5a41518b19460c6e8ee34f": {
                "dev_class": "tv",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Leeg 043AEC6",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "305452ce97c243c0a7b4ab2a4ebfe6e3": {
                "dev_class": "lamp",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Lamp piano 025F6819",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "bc0adbebc50d428d9444a5d805c89da9": {
                "dev_class": "watercooker",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Waterkoker 043AF7F",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "407aa1c1099d463c9137a3a9eda787fd": {
                "dev_class": "zz_misc",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "0043B013",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "2587a7fcdd7e482dab03fda256076b4b": {
                "dev_class": "zz_misc",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "00469CA1",
                "zigbee_mac_address": "ABCD012345670A16",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "a28e6f5afc0e4fc68498c1f03e82a052": {
                "dev_class": "lamp",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Lamp bank 25F67F8",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 4.19,
                    "electricity_consumed_interval": 0.62,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "24b2ed37c8964c73897db6340a39c129": {
                "dev_class": "router",
                "firmware": "2011-06-27T10:47:37+02:00",
                "hardware": "6539-0700-7325",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle+ type F",
                "name": "MK Netwerk 1A4455E",
                "zigbee_mac_address": "0123456789AB",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 4.63,
                    "electricity_consumed_interval": 0.65,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "f7b145c8492f4dd7a4de760456fdef3e": {
                "dev_class": "switching",
                "model": "Switchgroup",
                "name": "Test",
                "members": ["407aa1c1099d463c9137a3a9eda787fd"],
                "switches": {"relay": False},
            },
        }

        self.smile_setup = "stretch_v23"
        server, smile, client = await self.connect_wrapper(stretch=True)
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.3.12"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.device_items == 229

        switch_change = await self.tinker_switch(
            smile, "2587a7fcdd7e482dab03fda256076b4b"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile,
            "f7b145c8492f4dd7a4de760456fdef3e",
            ["407aa1c1099d463c9137a3a9eda787fd"],
        )
        assert switch_change

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v27_no_domain(self):
        """Test a legacy Stretch with firmware 2.7 setup, with no domain_objects."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Circle+
            "9b9bfdb3c7ad4ca5817ccaa235f1e094": {
                "dev_class": "zz_misc",
                "firmware": "2011-06-27T10:47:37+02:00",
                "hardware": "6539-0700-7326",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle+ type F",
                "name": "25881A2",
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A04",
                "sensors": {
                    "electricity_consumed": 13.3,
                    "electricity_consumed_interval": 7.77,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            # 76BF93
            "8b8d14b242e24cd789743c828b9a2ea9": {
                "sensors": {"electricity_consumed": 1.69},
                "switches": {"lock": False, "relay": True},
            },
            # 25F66AD
            "d0122ac66eba47b99d8e5fbd1e2f5932": {
                "sensors": {"electricity_consumed_interval": 2.21}
            },
        }

        self.smile_setup = "stretch_v27_no_domain"
        server, smile, client = await self.connect_wrapper(stretch=True)
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.7.18"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.device_items == 190
        _LOGGER.info(" # Assert no master thermostat")

        switch_change = await self.tinker_switch(
            smile, "8b8d14b242e24cd789743c828b9a2ea9"
        )
        assert switch_change

        await smile.close_connection()
        await self.disconnect(server, client)
