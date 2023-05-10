"""API to interact with the Open Thread Border Router REST API."""
from __future__ import annotations
from http import HTTPStatus
import json
from typing import Literal

import aiohttp
import voluptuous as vol  # type:ignore[import]

from .models import OperationalDataSet, Timestamp

# 5 minutes as recommended by
# https://github.com/openthread/openthread/discussions/8567#discussioncomment-4468920
PENDING_DATASET_DELAY_TIMER = 5 * 60 * 1000


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

    async def get_active_dataset(self) -> OperationalDataSet | None:
        """Get current active operational dataset.

        Returns None if there is no active operational dataset.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        response = await self._session.get(
            f"{self._url}/node/dataset/active",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NO_CONTENT:
            return None

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            return OperationalDataSet.from_json(await response.json())
        except (json.JSONDecodeError, vol.Error) as exc:
            raise OTBRError("unexpected API response") from exc

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

    async def _create_dataset(
        self, dataset: OperationalDataSet, dataset_type: Literal["active", "pending"]
    ) -> None:
        """Create active or pending operational dataset.

        The passed in OperationalDataSet does not need to be fully populated, any fields
        not set will be automatically set by the open thread border router.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        response = await self._session.post(
            f"{self._url}/node/dataset/{dataset_type}",
            json=dataset.as_json(),
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status != HTTPStatus.ACCEPTED:
            raise OTBRError(f"unexpected http status {response.status}")

    async def create_active_dataset(self, dataset: OperationalDataSet) -> None:
        """Create active operational dataset.

        The passed in OperationalDataSet does not need to be fully populated, any fields
        not set will be automatically set by the open thread border router.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        await self._create_dataset(dataset, "active")

    async def create_pending_dataset(self, dataset: OperationalDataSet) -> None:
        """Create pending operational dataset.

        The passed in OperationalDataSet does not need to be fully populated, any fields
        not set will be automatically set by the open thread border router.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        await self._create_dataset(dataset, "pending")

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

    async def set_channel(self, channel: int) -> None:
        """Change the channel

        The channel is changed by creating a new pending dataset based on the active
        dataset.
        """
        if not 11 <= channel <= 26:
            raise OTBRError(f"invalid channel {channel}")
        if not (dataset := await self.get_active_dataset()):
            raise OTBRError("router has no active dataset")

        if dataset.active_timestamp and dataset.active_timestamp.seconds is not None:
            dataset.active_timestamp.seconds += 1
        else:
            dataset.active_timestamp = Timestamp(False, 1, 0)
        dataset.channel = channel
        dataset.delay = PENDING_DATASET_DELAY_TIMER

        await self.create_pending_dataset(dataset)

    async def get_extended_address(self) -> bytes:
        """Get extended address (EUI-64).

        Raises if the http status is not 200 or if the response is invalid.
        """
        response = await self._session.get(
            f"{self._url}/node/ext-address",
            headers={"Accept": "application/json"},
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            return bytes.fromhex(await response.json())
        except ValueError as exc:
            raise OTBRError("unexpected API response") from exc
