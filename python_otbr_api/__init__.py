"""API to interact with the Open Thread Border Router REST API."""
from __future__ import annotations
from http import HTTPStatus

import aiohttp


class OTBRError(Exception):
    """Raised on error."""


class OTBR:  # pylint: disable=too-few-public-methods
    """Class to interact with the Open Thread Border Router REST API."""

    def __init__(
        self, url: str, session: aiohttp.ClientSession, timeout: int = 10
    ) -> None:
        """Initialize."""
        self._session = session
        self._url = url
        self._timeout = timeout

    def _raise_for_status(self, response: aiohttp.ClientResponse) -> None:
        """Raise if status >= 400."""
        try:
            response.raise_for_status()
        except aiohttp.ClientResponseError as exc:
            raise OTBRError(f"unexpected http status {response.status}") from exc

    async def get_active_dataset_tlvs(self) -> bytes | None:
        """Get current active operational dataset in TLVS format, or None.

        Returns None if there is no active operational dataset.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        response = await self._session.get(
            f"{self._url}/node/dataset/active",
            headers={"Accept": "text/plain"},
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        self._raise_for_status(response)
        if response.status == HTTPStatus.NO_CONTENT:
            return None

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            tmp = await response.read()
            return bytes.fromhex(tmp.decode("ASCII"))
        except ValueError as exc:
            raise OTBRError("unexpected API response") from exc
