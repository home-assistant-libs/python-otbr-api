"""API to interact with the Open Thread Border Router REST API."""
from __future__ import annotations
from http import HTTPStatus

import aiohttp

from .models import OperationalDataSet


class OTBRError(Exception):
    """Raised on error."""


class ThreadNetworkActiveError(OTBRError):
    """Raised on attempts to modify the active dataset when thread network is active."""


class OTBR:  # pylint: disable=too-few-public-methods
    """Class to interact with the Open Thread Border Router REST API."""

    def __init__(
        self, url: str, session: aiohttp.ClientSession, timeout: int = 10
    ) -> None:
        """Initialize."""
        self._session = session
        self._url = url
        self._timeout = timeout

    async def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the router."""

        response = await self._session.post(
            f"{self._url}/node/state",
            json="enable" if enabled else "disable",
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

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

        if response.status == HTTPStatus.NO_CONTENT:
            return None

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            return bytes.fromhex(await response.text("ASCII"))
        except ValueError as exc:
            raise OTBRError("unexpected API response") from exc

    async def create_active_dataset(self, dataset: OperationalDataSet) -> None:
        """Create active operational dataset.

        The passed in OperationalDataSet does not need to be fully populated, any fields
        not set will be automatically set by the open thread border router.
        Raises if the http status is 400 or higher or if the response is invalid.
        """

        response = await self._session.post(
            f"{self._url}/node/dataset/active",
            json=dataset.as_json(),
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status != HTTPStatus.ACCEPTED:
            raise OTBRError(f"unexpected http status {response.status}")

    async def set_active_dataset_tlvs(self, dataset: bytes) -> None:
        """Set current active operational dataset.

        Raises if the http status is 400 or higher or if the response is invalid.
        """

        response = await self._session.put(
            f"{self._url}/node/dataset/active",
            data=dataset.hex(),
            headers={"Content-Type": "text/plain"},
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status != HTTPStatus.ACCEPTED:
            raise OTBRError(f"unexpected http status {response.status}")
