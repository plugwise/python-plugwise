"""Test Plugwise module Adam related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise, pw_exceptions

SMILE_TYPE = "adam"


class TestPlugwiseAdam(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for Adam standalone, i.e. not combined with Anna or Jip."""

    @pytest.mark.asyncio
    async def test_connect_adam_zone_per_device(self):
        """Test an extensive setup of Adam with a zone per device."""
        self.smile_setup = "adam_zone_per_device"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        _LOGGER.error("HOI")
        _LOGGER.error(testdata)

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
        self.smile_setup = "adam_multiple_devices_per_zone"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
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
        self.smile_setup = "adam_heatpump_cooling"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
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
        self.smile_setup = "adam_onoff_cooling_fake_firmware"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
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
