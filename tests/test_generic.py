"""Test Plugwise module generic functionality."""

import asyncio
from unittest.mock import patch

from plugwise.smilecomm import SmileComm
import pytest

import aiohttp
from aiohttp import test_utils, web

from .test_init import _LOGGER, TestPlugwise, pw_exceptions


class TestPlugwiseGeneric(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for generic functionality."""

    @pytest.mark.asyncio
    async def test_fail_anna_connected_to_adam(self):
        """Test erroneous adam with anna system."""
        self.smile_setup = "anna_connected_to_adam"
        try:
            _server, _api, _client = await self.connect_wrapper()
            setup_result = False  # pragma: no cover
        except pw_exceptions.InvalidSetupError:
            setup_result = True
        assert setup_result

    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test P1 with invalid credentials setup."""
        self.smile_setup = "p1v4"
        try:
            await self.connect_wrapper(fail_auth=True)
            setup_result = False  # pragma: no cover
        except pw_exceptions.InvalidAuthentication:
            _LOGGER.debug("InvalidAuthentication raised successfully")
            setup_result = True
        assert setup_result

    @pytest.mark.asyncio
    async def test_connect_fail_firmware(self):
        """Test a P1 non existing firmware setup."""
        self.smile_setup = "fail_firmware"
        try:
            await self.connect_wrapper()
            setup_result = False  # pragma: no cover
        except pw_exceptions.UnsupportedDeviceError:
            setup_result = True
        assert setup_result

    # Test connect for timeout
    @patch(
        "plugwise.smilecomm.ClientSession.get",
        side_effect=aiohttp.ServerTimeoutError,
    )
    @pytest.mark.asyncio
    async def test_connect_timeout(self, timeout_test):
        """Wrap connect to raise timeout during get."""
        # pylint: disable=unused-variable
        try:
            self.smile_setup = "p1v4"
            (
                server,
                api,
                client,
            ) = await self.connect_wrapper()
            setup_result = False  # pragma: no cover
        except pw_exceptions.PlugwiseException:
            setup_result = True
        assert setup_result

    @staticmethod
    async def _start_rules_server(calls, put_handler):
        """Start a mock Smile that records the method and body of each request."""

        async def put(request):
            calls.append(("PUT", await request.text()))
            return await put_handler(request, calls)

        async def get(request):
            calls.append(("GET", await request.text()))
            return web.Response(text="<rules />")

        app = web.Application()
        if put_handler is not None:
            app.router.add_route("PUT", "/core/rules{tail:.*}", put)
        app.router.add_route("GET", "/core/rules{tail:.*}", get)
        server = test_utils.TestServer(
            app, port=test_utils.unused_port(), scheme="http", host="127.0.0.1"
        )
        await server.start_server()
        return server

    @pytest.mark.asyncio
    async def test_put_retried_as_put_after_504(self):
        """Test that a retried PUT keeps its method and body."""
        calls = []

        async def timeout_once(request, calls):
            if len(calls) == 1:
                raise web.HTTPGatewayTimeout()
            raise web.HTTPAccepted(text="<xml />")

        server = await self._start_rules_server(calls, timeout_once)
        comm = SmileComm(
            server.host, "pw", server.port, 10, username="smile", websession=None
        )
        data = "<rules><rule id='abc'></rule></rules>"
        try:
            # pylint: disable-next=protected-access
            await comm._request("/core/rules;id=abc", method="put", data=data)
        finally:
            await comm.close_connection()
            await server.close()
        assert calls == [("PUT", data), ("PUT", data)]

    @pytest.mark.asyncio
    async def test_put_dropped_raises(self):
        """Test that a PUT failing on every retry raises instead of turning into a GET."""
        calls = []

        async def drop_connection(request, calls):
            request.transport.close()
            await asyncio.sleep(0.1)

        server = await self._start_rules_server(calls, drop_connection)
        comm = SmileComm(
            server.host, "pw", server.port, 10, username="smile", websession=None
        )
        try:
            with pytest.raises(pw_exceptions.ConnectionFailedError):
                # pylint: disable-next=protected-access
                await comm._request(
                    "/core/rules;id=abc", method="put", data="<rules />"
                )
        finally:
            await comm.close_connection()
            await server.close()
        assert calls and all(call == ("PUT", "<rules />") for call in calls)

    @pytest.mark.asyncio
    async def test_put_not_allowed_raises(self):
        """Test that a 405 on PUT raises."""
        calls = []
        server = await self._start_rules_server(calls, None)
        comm = SmileComm(
            server.host, "pw", server.port, 10, username="smile", websession=None
        )
        try:
            with pytest.raises(pw_exceptions.ConnectionFailedError):
                # pylint: disable-next=protected-access
                await comm._request(
                    "/core/rules;id=abc", method="put", data="<rules />"
                )
        finally:
            await comm.close_connection()
            await server.close()
        assert not calls
