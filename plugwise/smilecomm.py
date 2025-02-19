"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile communication protocol helpers.
"""

from __future__ import annotations

from plugwise.constants import LOGGER
from plugwise.exceptions import (
    ConnectionFailedError,
    InvalidAuthentication,
    InvalidXMLError,
    ResponseError,
)
from plugwise.util import escape_illegal_xml_characters

# This way of importing aiohttp is because of patch/mocking in testing (aiohttp timeouts)
from aiohttp import BasicAuth, ClientError, ClientResponse, ClientSession, ClientTimeout
from defusedxml import ElementTree as etree


class SmileComm:
    """The SmileComm class."""

    def __init__(
        self,
        host: str,
        password: str,
        port: int,
        timeout: int,
        username: str,
        websession: ClientSession | None,
    ) -> None:
        """Set the constructor for this class."""
        if not websession:
            aio_timeout = ClientTimeout(total=timeout)
            self._websession = ClientSession(timeout=aio_timeout)
        else:
            self._websession = websession

        # Quickfix IPv6 formatting, not covering
        if host.count(":") > 2:  # pragma: no cover
            host = f"[{host}]"

        self._auth = BasicAuth(username, password=password)
        self._endpoint = f"http://{host}:{str(port)}"  # Sensitive

    async def _request(
        self,
        command: str,
        retry: int = 3,
        method: str = "get",
        data: str | None = None,
    ) -> etree.Element:
        """Get/put/delete data from a give URL."""
        resp: ClientResponse
        url = f"{self._endpoint}{command}"
        try:
            match method:
                case "delete":
                    resp = await self._websession.delete(url, auth=self._auth)
                case "get":
                    # Work-around for Stretchv2, should not hurt the other smiles
                    headers = {"Accept-Encoding": "gzip"}
                    resp = await self._websession.get(
                        url, headers=headers, auth=self._auth
                    )
                case "post":
                    headers = {"Content-type": "text/xml"}
                    resp = await self._websession.post(
                        url,
                        headers=headers,
                        data=data,
                        auth=self._auth,
                    )
                case "put":
                    headers = {"Content-type": "text/xml"}
                    resp = await self._websession.put(
                        url,
                        headers=headers,
                        data=data,
                        auth=self._auth,
                    )
        except (
            ClientError
        ) as exc:  # ClientError is an ancestor class of ServerTimeoutError
            if retry < 1:
                LOGGER.warning(
                    "Failed sending %s %s to Plugwise Smile, error: %s",
                    method,
                    command,
                    exc,
                )
                raise ConnectionFailedError from exc
            return await self._request(command, retry - 1)

        if resp.status == 504:
            if retry < 1:
                LOGGER.warning(
                    "Failed sending %s %s to Plugwise Smile, error: %s",
                    method,
                    command,
                    "504 Gateway Timeout",
                )
                raise ConnectionFailedError
            return await self._request(command, retry - 1)

        return await self._request_validate(resp, method)

    async def _request_validate(
        self, resp: ClientResponse, method: str
    ) -> etree.Element:
        """Helper-function for _request(): validate the returned data."""
        match resp.status:
            case 200:
                # Cornercases for server not responding with 202
                if method in ("post", "put"):
                    return
            case 202:
                # Command accepted gives empty body with status 202
                return
            case 401:
                msg = (
                    "Invalid Plugwise login, please retry with the correct credentials."
                )
                LOGGER.error("%s", msg)
                raise InvalidAuthentication
            case 405:
                msg = "405 Method not allowed."
                LOGGER.error("%s", msg)
                raise ConnectionFailedError

        if not (result := await resp.text()) or (
            "<error>" in result and "Not started" not in result
        ):
            LOGGER.warning("Smile response empty or error in %s", result)
            raise ResponseError

        try:
            # Encode to ensure utf8 parsing
            xml = etree.XML(escape_illegal_xml_characters(result).encode())
        except etree.ParseError as exc:
            LOGGER.warning("Smile returns invalid XML for %s", self._endpoint)
            raise InvalidXMLError from exc

        return xml

    async def close_connection(self) -> None:
        """Close the Plugwise connection."""
        await self._websession.close()
