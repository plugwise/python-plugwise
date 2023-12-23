"""Test Plugwise module P1 related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise


class TestPlugwiseP1(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for P1."""

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2(self):
        """Test a legacy P1 device."""
        testdata = {
            "aaaa0000aaaa0000aaaa0000aaaa00aa": {
                "dev_class": "gateway",
                "firmware": "2.5.9",
                "location": "938696c4bcdb4b8a9a595cb38ed43913",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
            },
            "938696c4bcdb4b8a9a595cb38ed43913": {
                "dev_class": "smartmeter",
                "location": "938696c4bcdb4b8a9a595cb38ed43913",
                "model": "Ene5\\T210-DESMR5.0",
                "name": "P1",
                "vendor": "Ene5\\T210-DESMR5.0",
                "sensors": {
                    "net_electricity_point": 458,
                    "electricity_consumed_point": 458,
                    "net_electricity_cumulative": 1019.201,
                    "electricity_consumed_peak_cumulative": 1155.195,
                    "electricity_consumed_off_peak_cumulative": 1642.74,
                    "electricity_consumed_peak_interval": 250,
                    "electricity_consumed_off_peak_interval": 0,
                    "electricity_produced_point": 0,
                    "electricity_produced_peak_cumulative": 1296.136,
                    "electricity_produced_off_peak_cumulative": 482.598,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "gas_consumed_cumulative": 584.433,
                    "gas_consumed_interval": 0.016,
                },
            },
        }

        self.smile_setup = "smile_p1_v2"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.5.9"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "aaaa0000aaaa0000aaaa0000aaaa00aa"
        assert smile.device_items == 26
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2_2(self):
        """Test another legacy P1 device."""
        testdata = {
            "aaaa0000aaaa0000aaaa0000aaaa00aa": {
                "dev_class": "gateway",
                "firmware": "2.5.9",
                "location": "199aa40f126840f392983d171374ab0b",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
            },
            "199aa40f126840f392983d171374ab0b": {
                "dev_class": "smartmeter",
                "location": "199aa40f126840f392983d171374ab0b",
                "model": "Ene5\\T210-DESMR5.0",
                "name": "P1",
                "vendor": "Ene5\\T210-DESMR5.0",
                "sensors": {
                    "net_electricity_point": 458,
                    "electricity_consumed_point": 458,
                    "net_electricity_cumulative": 1019.201,
                    "electricity_consumed_peak_cumulative": 1155.195,
                    "electricity_consumed_off_peak_cumulative": 1642.74,
                    "electricity_consumed_peak_interval": 250,
                    "electricity_consumed_off_peak_interval": 0,
                    "electricity_produced_point": 0,
                    "electricity_produced_peak_cumulative": 1296.136,
                    "electricity_produced_off_peak_cumulative": 482.598,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "gas_consumed_cumulative": 584.433,
                    "gas_consumed_interval": 0.016,
                },
            },
        }
        testdata_updated = {
            "199aa40f126840f392983d171374ab0b": {
                "sensors": {
                    "net_electricity_point": -2248,
                    "electricity_consumed_point": 0,
                    "net_electricity_cumulative": 1019.101,
                    "electricity_consumed_peak_cumulative": 1155.295,
                    "electricity_consumed_off_peak_cumulative": 1642.84,
                    "electricity_produced_point": 2248,
                    "electricity_produced_peak_cumulative": 1296.336,
                    "electricity_produced_off_peak_cumulative": 482.698,
                    "gas_consumed_cumulative": 585.433,
                    "gas_consumed_interval": 0,
                },
            },
        }

        self.smile_setup = "smile_p1_v2_2"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.5.9"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.device_items == 26
        assert not self.notifications

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        self.smile_setup = "updated/smile_p1_v2_2"
        await self.device_test(
            smile, "2022-05-16 00:00:01", testdata_updated, initialize=False
        )

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4(self):
        """Test a P1 firmware 4 setup."""
        testdata = {
            "a455b61e52394b2db5081ce025a430f3": {
                "dev_class": "gateway",
                "firmware": "4.1.1",
                "hardware": "AME Smile 2.0 board",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": True},
            },
            "ba4de7613517478da82dd9b6abea36af": {
                "dev_class": "smartmeter",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "model": "KFM5KAIFA-METER",
                "name": "P1",
                "vendor": "SHENZHEN KAIFA TECHNOLOGY CHENGDU CO.",
                "available": False,
                "sensors": {
                    "net_electricity_point": 548,
                    "electricity_consumed_peak_point": 548,
                    "electricity_consumed_off_peak_point": 0,
                    "net_electricity_cumulative": 20983.453,
                    "electricity_consumed_peak_cumulative": 9067.554,
                    "electricity_consumed_off_peak_cumulative": 11915.899,
                    "electricity_consumed_peak_interval": 335,
                    "electricity_consumed_off_peak_interval": 0,
                    "electricity_produced_peak_point": 0,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 0.0,
                    "electricity_produced_off_peak_cumulative": 0.0,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                },
            },
        }

        self.smile_setup = "p1v4"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.1.1"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "a455b61e52394b2db5081ce025a430f3"
        assert smile.device_items == 29
        assert "97a04c0c263049b29350a660b4cdd01e" in self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4_442_single(self):
        """Test a P1 firmware 4.4 single-phase setup."""
        testdata = {
            "a455b61e52394b2db5081ce025a430f3": {
                "dev_class": "gateway",
                "firmware": "4.4.2",
                "hardware": "AME Smile 2.0 board",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "ba4de7613517478da82dd9b6abea36af": {
                "dev_class": "smartmeter",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "model": "KFM5KAIFA-METER",
                "name": "P1",
                "vendor": "SHENZHEN KAIFA TECHNOLOGY （CHENGDU） CO., LTD.",
                "available": True,
                "sensors": {
                    "net_electricity_point": 421,
                    "electricity_consumed_peak_point": 0,
                    "electricity_consumed_off_peak_point": 421,
                    "net_electricity_cumulative": 31610.113,
                    "electricity_consumed_peak_cumulative": 13966.608,
                    "electricity_consumed_off_peak_cumulative": 17643.505,
                    "electricity_consumed_peak_interval": 0,
                    "electricity_consumed_off_peak_interval": 21,
                    "electricity_produced_peak_point": 0,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 0.0,
                    "electricity_produced_off_peak_cumulative": 0.0,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "electricity_phase_one_consumed": 413,
                    "electricity_phase_one_produced": 0,
                },
            },
        }
        testdata_updated = {
            "ba4de7613517478da82dd9b6abea36af": {
                "sensors": {
                    "net_electricity_point": -2248,
                    "electricity_consumed_peak_point": 0,
                    "electricity_consumed_off_peak_point": 0,
                    "electricity_consumed_peak_interval": 0,
                    "electricity_consumed_off_peak_interval": 0,
                    "electricity_produced_peak_point": 2248,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 6.543,
                    "electricity_produced_off_peak_cumulative": 0.0,
                    "electricity_produced_peak_interval": 1345,
                    "electricity_produced_off_peak_interval": 0,
                    "electricity_phase_one_consumed": 0,
                    "electricity_phase_one_produced": 1998,
                },
            },
        }

        self.smile_setup = "p1v4_442_single"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.4.2"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "a455b61e52394b2db5081ce025a430f3"
        assert smile.device_items == 31
        assert not self.notifications

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        self.smile_setup = "updated/p1v4_442_single"
        await self.device_test(
            smile, "2022-05-16 00:00:01", testdata_updated, initialize=False
        )

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4_442_triple(self):
        """Test a P1 firmware 4 3-phase setup."""
        testdata = {
            "03e65b16e4b247a29ae0d75a78cb492e": {
                "dev_class": "gateway",
                "firmware": "4.4.2",
                "hardware": "AME Smile 2.0 board",
                "location": "03e65b16e4b247a29ae0d75a78cb492e",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": True},
            },
            "b82b6b3322484f2ea4e25e0bd5f3d61f": {
                "dev_class": "smartmeter",
                "location": "03e65b16e4b247a29ae0d75a78cb492e",
                "model": "XMX5LGF0010453051839",
                "name": "P1",
                "vendor": "XEMEX NV",
                "available": True,
                "sensors": {
                    "net_electricity_point": 5553,
                    "electricity_consumed_peak_point": 0,
                    "electricity_consumed_off_peak_point": 5553,
                    "net_electricity_cumulative": 231866.539,
                    "electricity_consumed_peak_cumulative": 161328.641,
                    "electricity_consumed_off_peak_cumulative": 70537.898,
                    "electricity_consumed_peak_interval": 0,
                    "electricity_consumed_off_peak_interval": 314,
                    "electricity_produced_peak_point": 0,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 0.0,
                    "electricity_produced_off_peak_cumulative": 0.0,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "electricity_phase_one_consumed": 1763,
                    "electricity_phase_two_consumed": 1703,
                    "electricity_phase_three_consumed": 2080,
                    "electricity_phase_one_produced": 0,
                    "electricity_phase_two_produced": 0,
                    "electricity_phase_three_produced": 0,
                    "gas_consumed_cumulative": 16811.37,
                    "gas_consumed_interval": 0.06,
                    "voltage_phase_one": 233.2,
                    "voltage_phase_two": 234.4,
                    "voltage_phase_three": 234.7,
                },
            },
        }

        self.smile_setup = "p1v4_442_triple"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.4.2"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "03e65b16e4b247a29ae0d75a78cb492e"
        assert smile.device_items == 40
        assert self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)
