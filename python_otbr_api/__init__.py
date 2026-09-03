"""API to interact with the Open Thread Border Router REST API."""

from __future__ import annotations

from enum import Enum, auto
from http import HTTPStatus
from typing import Any
import json
import logging

import aiohttp
import voluptuous as vol  # type: ignore[import]

from .models import (
    ActiveDataSet,
    EphemeralKeyActivationResult,
    EphemeralKeyState,
    EphemeralKeyStatus,
    PendingDataSet,
    Timestamp,
)

# 5 minutes as recommended by
# https://github.com/openthread/openthread/discussions/8567#discussioncomment-4468920
PENDING_DATASET_DELAY_TIMER = 5 * 60 * 1000

_LOGGER = logging.getLogger(__name__)

# OTBR flipped the REST API from PascalCase to camelCase in ot-br-posix
# PR #2514 (Sept 2025). The models speak camelCase internally; this table
# translates both directions at the HTTP boundary for legacy servers.
_CAMEL_TO_PASCAL: dict[str, str] = {
    # Timestamp
    "authoritative": "Authoritative",
    "seconds": "Seconds",
    "ticks": "Ticks",
    # SecurityPolicy
    "autonomousEnrollment": "AutonomousEnrollment",
    "commercialCommissioning": "CommercialCommissioning",
    "externalCommissioning": "ExternalCommissioning",
    "nativeCommissioning": "NativeCommissioning",
    "networkKeyProvisioning": "NetworkKeyProvisioning",
    "nonCcmRouters": "NonCcmRouters",
    "obtainNetworkKey": "ObtainNetworkKey",
    "rotationTime": "RotationTime",
    "routers": "Routers",
    "tobleLink": "TobleLink",
    # ActiveDataSet
    "activeTimestamp": "ActiveTimestamp",
    "channelMask": "ChannelMask",
    "channel": "Channel",
    "extPanId": "ExtPanId",
    "meshLocalPrefix": "MeshLocalPrefix",
    "networkKey": "NetworkKey",
    "networkName": "NetworkName",
    "panId": "PanId",
    "pskc": "PSKc",
    "securityPolicy": "SecurityPolicy",
    # PendingDataSet
    "activeDataset": "ActiveDataset",
    "delay": "Delay",
    "pendingTimestamp": "PendingTimestamp",
}
_PASCAL_TO_CAMEL: dict[str, str] = {v: k for k, v in _CAMEL_TO_PASCAL.items()}


class KeyFormat(Enum):
    """JSON key format used by the OTBR REST API.

    PASCAL_CASE is the pre-Sept-2025 wire format (ot-br-posix pre-#2514):
    writes are rewritten to PascalCase. CAMEL_CASE covers every post-flip
    server, including the Sept-2025..April-2026 window where some keys
    (e.g. `Routers` in SecurityPolicy) still came back PascalCase — reads
    always run through the PascalCase normalization table so those
    stragglers are picked up transparently.
    """

    CAMEL_CASE = "camel"
    PASCAL_CASE = "pascal"


class _UndefinedType(Enum):
    """Singleton sentinel distinguishing "not probed yet" from a probed None."""

    UNDEFINED = auto()


_UNDEFINED = _UndefinedType.UNDEFINED


class OTBRError(Exception):
    """Raised on error."""


class FactoryResetNotSupportedError(OTBRError):
    """Raised when attempting to factory reset a router which does not support it."""


class GetBorderAgentIdNotSupportedError(OTBRError):
    """Raised when attempting to get the agent ID if the router does not support it."""


class ThreadNetworkActiveError(OTBRError):
    """Raised on attempts to modify the active dataset when thread network is active."""


class EphemeralKeyNotSupportedError(OTBRError):
    """Raised when the router does not support the ephemeral key (ePSKc) feature."""


class EphemeralKeyConflictError(OTBRError):
    """Raised when activating an ephemeral key while the feature is disabled or a
    key is already active."""


class PendingDatasetConflictError(OTBRError):
    """Raised when a pending dataset write is refused because one is in place.

    Its own type rather than a plain OTBRError: the caller's next step is
    different from the one a transport or protocol failure calls for, since
    nothing was written and the state that made the write wrong is readable.
    """


def _rewrite_keys(data: Any, mapping: dict[str, str]) -> Any:
    """Recursively rename dict keys according to mapping; pass through others."""
    if not isinstance(data, dict):
        return data
    return {mapping.get(k, k): _rewrite_keys(v, mapping) for k, v in data.items()}


class OTBR:  # pylint: disable=too-many-public-methods
    """Class to interact with the Open Thread Border Router REST API."""

    def __init__(
        self,
        url: str,
        session: aiohttp.ClientSession,
        timeout: int = 10,
        *,
        key_format: KeyFormat | None = None,
    ) -> None:
        """Initialize."""
        self._session = session
        self._url = url
        self._timeout = timeout
        self._key_format = key_format
        self._api_version: str | None | _UndefinedType = _UNDEFINED

    async def _maybe_detect_key_format(self) -> None:
        """Probe the OTBR REST API to determine the JSON key format."""
        if self._key_format is not None:
            return

        response = await self._session.get(
            f"{self._url}/api/actions",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.OK:
            self._key_format = KeyFormat.CAMEL_CASE
        elif response.status == HTTPStatus.NOT_FOUND:
            self._key_format = KeyFormat.PASCAL_CASE
        else:
            raise OTBRError(
                f"could not detect OTBR version: unexpected http status "
                f"{response.status}"
            )

        _LOGGER.debug("Detected OTBR JSON key format: %s", self._key_format)

    def _encode(self, data: dict) -> dict:
        """Rewrite a camelCase body to the detected wire format."""
        if self._key_format == KeyFormat.PASCAL_CASE:
            return _rewrite_keys(data, _CAMEL_TO_PASCAL)
        return data

    def _decode(self, data: dict) -> dict:
        """Normalize a wire response body to camelCase."""

        # Runs unconditionally: camelCase keys aren't in the table so they pass through
        # untouched, while any PascalCase stragglers (full legacy or transition-era
        # leftovers like `Routers`) get fixed.
        return _rewrite_keys(data, _PASCAL_TO_CAMEL)

    async def factory_reset(self) -> None:
        """Factory reset the router."""
        await self._maybe_detect_key_format()
        response = await self._session.delete(
            f"{self._url}/node",
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if response.status == HTTPStatus.METHOD_NOT_ALLOWED:
            raise FactoryResetNotSupportedError

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

    async def get_border_agent_id(self) -> bytes:
        """Get the border agent ID."""
        await self._maybe_detect_key_format()
        response = await self._session.get(
            f"{self._url}/node/ba-id",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NOT_FOUND:
            raise GetBorderAgentIdNotSupportedError

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            return bytes.fromhex(await response.json())
        except ValueError as exc:
            raise OTBRError("unexpected API response") from exc

    async def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the router."""
        await self._maybe_detect_key_format()
        response = await self._session.put(
            f"{self._url}/node/state",
            json="enable" if enabled else "disable",
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

    async def get_active_dataset(self) -> ActiveDataSet | None:
        """Get current active operational dataset.

        Returns None if there is no active operational dataset.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        await self._maybe_detect_key_format()
        response = await self._session.get(
            f"{self._url}/node/dataset/active",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NO_CONTENT:
            return None

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            return ActiveDataSet.from_json(self._decode(await response.json()))
        except (json.JSONDecodeError, vol.Error) as exc:
            raise OTBRError("unexpected API response") from exc

    async def get_active_dataset_tlvs(self) -> bytes | None:
        """Get current active operational dataset in TLVS format, or None.

        Returns None if there is no active operational dataset.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        await self._maybe_detect_key_format()
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

    async def get_pending_dataset_tlvs(self) -> bytes | None:
        """Get current pending operational dataset in TLVS format, or None.

        Returns None if there is no pending operational dataset.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        await self._maybe_detect_key_format()
        response = await self._session.get(
            f"{self._url}/node/dataset/pending",
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

    async def create_active_dataset(self, dataset: ActiveDataSet) -> None:
        """Create active operational dataset.

        The passed in ActiveDataSet does not need to be fully populated, any fields
        not set will be automatically set by the open thread border router.
        Raises if the http status is 400 or higher or if the response is invalid.
        """
        await self._maybe_detect_key_format()
        response = await self._session.put(
            f"{self._url}/node/dataset/active",
            json=self._encode(dataset.as_json()),
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status not in (HTTPStatus.CREATED, HTTPStatus.OK):
            raise OTBRError(f"unexpected http status {response.status}")

    async def delete_active_dataset(self) -> None:
        """Delete active operational dataset."""
        await self._maybe_detect_key_format()
        response = await self._session.delete(
            f"{self._url}/node/dataset/active",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

    async def create_pending_dataset(self, dataset: PendingDataSet) -> None:
        """Create pending operational dataset.

        The passed in PendingDataSet does not need to be fully populated, any fields
        not set will be automatically set by the open thread border router.

        A write while a pending dataset is in flight is refused outright, for the
        same reasons set_pending_dataset_tlvs refuses it: superseding one races
        the delay timer on every device that already holds the old dataset, so a
        late replacement can split the mesh, and it would also silently undo
        whatever the in-flight dataset was doing, such as a channel change.

        The check runs locally first, and again on the border router for one
        that honors If-None-Match on this endpoint
        (https://github.com/openthread/ot-br-posix/pull/3552), where it is
        atomic with the write; older border routers ignore the header.

        Raises PendingDatasetConflictError when either check refuses the write,
        and OTBRError if the http status is 400 or higher for any other reason
        or the response is invalid.
        """
        if await self.get_pending_dataset_tlvs() is not None:
            raise PendingDatasetConflictError("a pending dataset is already in place")
        await self._maybe_detect_key_format()
        response = await self._session.put(
            f"{self._url}/node/dataset/pending",
            json=self._encode(dataset.as_json()),
            headers={"If-None-Match": "*"},
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status == HTTPStatus.PRECONDITION_FAILED:
            raise PendingDatasetConflictError("a pending dataset is already in place")
        if response.status not in (HTTPStatus.CREATED, HTTPStatus.OK):
            raise OTBRError(f"unexpected http status {response.status}")

    async def delete_pending_dataset(self) -> None:
        """Delete pending operational dataset."""
        await self._maybe_detect_key_format()
        response = await self._session.delete(
            f"{self._url}/node/dataset/pending",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

    async def set_active_dataset_tlvs(self, dataset: bytes) -> None:
        """Set current active operational dataset.

        Raises if the http status is 400 or higher or if the response is invalid.
        """
        await self._maybe_detect_key_format()
        response = await self._session.put(
            f"{self._url}/node/dataset/active",
            data=dataset.hex(),
            headers={"Content-Type": "text/plain"},
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status not in (HTTPStatus.CREATED, HTTPStatus.OK):
            raise OTBRError(f"unexpected http status {response.status}")

    async def set_pending_dataset_tlvs(self, dataset: bytes) -> None:
        """Set the pending operational dataset, when none is in place yet.

        A write while a pending dataset is in flight is refused outright.
        Superseding one is never safe to do implicitly: the replacement races
        the delay timer on every device that already holds the old dataset, so
        a late replacement can split the mesh, and it would also silently undo
        whatever the in-flight dataset was doing, such as a channel change.
        A caller that finds the write refused should surface that to whoever
        asked for it, not retry.

        The check runs locally first, and again on the border router for one
        that honors If-None-Match on this endpoint
        (https://github.com/openthread/ot-br-posix/pull/3552), where it is
        atomic with the write; older border routers ignore the header.

        Raises PendingDatasetConflictError when either check refuses the
        write, and OTBRError if the http status is 400 or higher for any
        other reason or the response is invalid.
        """
        if await self.get_pending_dataset_tlvs() is not None:
            raise PendingDatasetConflictError("a pending dataset is already in place")
        await self._maybe_detect_key_format()
        response = await self._session.put(
            f"{self._url}/node/dataset/pending",
            data=dataset.hex(),
            headers={"Content-Type": "text/plain", "If-None-Match": "*"},
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if response.status == HTTPStatus.CONFLICT:
            raise ThreadNetworkActiveError
        if response.status == HTTPStatus.PRECONDITION_FAILED:
            raise PendingDatasetConflictError("a pending dataset is already in place")
        if response.status not in (HTTPStatus.CREATED, HTTPStatus.OK):
            raise OTBRError(f"unexpected http status {response.status}")

    async def set_channel(
        self, channel: int, delay: int = PENDING_DATASET_DELAY_TIMER
    ) -> None:
        """Change the channel

        The channel is changed by creating a new pending dataset based on the active
        dataset. If a pending dataset is already in place, create_pending_dataset
        refuses the write and raises PendingDatasetConflictError: stamping from the
        active dataset alone would make the mesh silently ignore it while the router
        accepts the write, and superseding the pending dataset would race its delay
        timer on devices that miss the update.
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
        pending_dataset = PendingDataSet(active_dataset=dataset, delay=delay)

        await self.create_pending_dataset(pending_dataset)

    async def get_extended_address(self) -> bytes:
        """Get extended address (EUI-64).

        Raises if the http status is not 200 or if the response is invalid.
        """
        await self._maybe_detect_key_format()
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

    async def get_ephemeral_key_enabled(self) -> bool:
        """Get whether the ephemeral key (ePSKc) feature is enabled.

        Raises EphemeralKeyNotSupportedError if the router does not support
        the ephemeral key feature.
        """
        await self._maybe_detect_key_format()
        response = await self._session.get(
            f"{self._url}/node/ba-epskc/state",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NOT_FOUND:
            raise EphemeralKeyNotSupportedError

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            return (await response.json()) == "enabled"
        except ValueError as exc:
            raise OTBRError("unexpected API response") from exc

    async def set_ephemeral_key_enabled(self, enabled: bool) -> None:
        """Enable or disable the ephemeral key (ePSKc) feature.

        The feature must be enabled before an ephemeral key can be activated.
        Raises EphemeralKeyNotSupportedError if the router does not support
        the ephemeral key feature.
        """
        await self._maybe_detect_key_format()
        response = await self._session.put(
            f"{self._url}/node/ba-epskc/state",
            json="enable" if enabled else "disable",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NOT_FOUND:
            raise EphemeralKeyNotSupportedError

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

    async def get_ephemeral_key_status(self) -> EphemeralKeyStatus:
        """Get the status of the current ephemeral key (ePSKc) session.

        Raises EphemeralKeyNotSupportedError if the router does not support
        the ephemeral key feature.
        """
        await self._maybe_detect_key_format()
        response = await self._session.get(
            f"{self._url}/node/ba-epskc/key",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NOT_FOUND:
            raise EphemeralKeyNotSupportedError

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            data = await response.json()
            return EphemeralKeyStatus(
                state=EphemeralKeyState(data["state"]), port=data["port"]
            )
        except (ValueError, KeyError) as exc:
            raise OTBRError("unexpected API response") from exc

    async def activate_ephemeral_key(
        self, lifetime: int | None = None, port: int | None = None
    ) -> EphemeralKeyActivationResult:
        """Generate and activate an ephemeral key (ePSKc).

        Returns the generated 9-digit Thread Administration Passcode (TAP)
        and the UDP port the border agent is listening on for the ePSKc
        session. `lifetime` is the key lifetime in milliseconds and `port`
        the UDP port to use; both default to the router's own defaults when
        omitted.

        Raises EphemeralKeyNotSupportedError if the router does not support
        the ephemeral key feature, and EphemeralKeyConflictError if the
        feature is disabled or a key is already active.
        """
        await self._maybe_detect_key_format()
        body: dict[str, int] = {}
        if lifetime is not None:
            body["lifetime"] = lifetime
        if port is not None:
            body["port"] = port

        response = await self._session.post(
            f"{self._url}/node/ba-epskc/key",
            json=body,
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NOT_FOUND:
            raise EphemeralKeyNotSupportedError
        if response.status == HTTPStatus.CONFLICT:
            raise EphemeralKeyConflictError
        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            data = await response.json()
            return EphemeralKeyActivationResult(tap=data["tap"], port=data["port"])
        except (ValueError, KeyError) as exc:
            raise OTBRError("unexpected API response") from exc

    async def deactivate_ephemeral_key(self) -> None:
        """Deactivate the currently active ephemeral key (ePSKc), if any.

        Raises EphemeralKeyNotSupportedError if the router does not support
        the ephemeral key feature.
        """
        await self._maybe_detect_key_format()
        response = await self._session.delete(
            f"{self._url}/node/ba-epskc/key",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NOT_FOUND:
            raise EphemeralKeyNotSupportedError

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

    async def get_coprocessor_version(self) -> str:
        """Get the coprocessor firmware version.

        Raises if the http status is not 200 or if the response is invalid.
        """
        await self._maybe_detect_key_format()
        response = await self._session.get(
            f"{self._url}/node/coprocessor/version",
            headers={"Accept": "application/json"},
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            return await response.json()
        except ValueError as exc:
            raise OTBRError("unexpected API response") from exc

    async def get_api_version(self) -> str | None:
        """Get the OTBR REST API's semantic version.

        Reads /.well-known/thread/br-rest (ot-br-posix PR #3330). Returns
        None on routers that don't expose it. Raises OTBRError if the
        endpoint exists but responds with an unexpected status or a
        malformed body.
        """
        if self._api_version is not _UNDEFINED:
            return self._api_version

        response = await self._session.get(
            f"{self._url}/.well-known/thread/br-rest",
            timeout=aiohttp.ClientTimeout(total=self._timeout),
        )

        if response.status == HTTPStatus.NOT_FOUND:
            self._api_version = None
            return None

        if response.status != HTTPStatus.OK:
            raise OTBRError(f"unexpected http status {response.status}")

        try:
            data = await response.json()
            api_version: str = data["api"]["version"]
        except (ValueError, KeyError, TypeError) as exc:
            raise OTBRError("unexpected API response") from exc

        self._api_version = api_version
        _LOGGER.debug("Detected OTBR REST API version: %s", api_version)
        return api_version
