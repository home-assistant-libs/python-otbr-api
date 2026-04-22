"""Tests for version detection and the camelCase wire format."""

from http import HTTPStatus
from typing import Any

import pytest
import python_otbr_api
from python_otbr_api import KeyFormat, VersionNotDetectedError

from tests.test_util.aiohttp import AiohttpClientMocker

BASE_URL = "http://core-openthread-border-router:8081"

DATASET_JSON_CAMEL: dict[str, Any] = {
    "activeTimestamp": {"authoritative": False, "seconds": 1, "ticks": 0},
    "channelMask": 134215680,
    "channel": 15,
    "extPanId": "8478E3379E047B92",
    "meshLocalPrefix": "fd89:bde7:42ed:a901::/64",
    "networkKey": "96271D6ECC78749114AB6A591E0D06F1",
    "networkName": "OpenThread HA",
    "panId": 33991,
    "pskc": "9760C89414D461AC717DCD105EB87E5B",
    "securityPolicy": {
        "autonomousEnrollment": False,
        "commercialCommissioning": False,
        "externalCommissioning": True,
        "nativeCommissioning": True,
        "networkKeyProvisioning": False,
        "nonCcmRouters": False,
        "obtainNetworkKey": True,
        "rotationTime": 672,
        "routers": True,
        "tobleLink": True,
    },
}


async def test_detect_version_camel(aioclient_mock: AiohttpClientMocker) -> None:
    """A 200 on /api/actions indicates a post-flip (camelCase) server."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(
        f"{BASE_URL}/api/actions", status=HTTPStatus.OK, json={"data": []}
    )

    assert await otbr.detect_version() == KeyFormat.CAMEL_CASE


async def test_detect_version_pascal(aioclient_mock: AiohttpClientMocker) -> None:
    """A 404 on /api/actions indicates the legacy PascalCase REST API."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/api/actions", status=HTTPStatus.NOT_FOUND)

    assert await otbr.detect_version() == KeyFormat.PASCAL_CASE


async def test_detect_version_unexpected_status(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Any status other than 200/404 is an inconclusive probe and raises."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(
        f"{BASE_URL}/api/actions", status=HTTPStatus.INTERNAL_SERVER_ERROR
    )

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.detect_version()


async def test_method_without_detect_raises(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Methods refuse to run before detect_version has been called."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    with pytest.raises(VersionNotDetectedError):
        await otbr.factory_reset()


async def test_constructor_key_format_skips_detection(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Passing key_format at construction time bypasses the probe."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.CAMEL_CASE
    )
    aioclient_mock.delete(f"{BASE_URL}/node", status=HTTPStatus.OK)
    await otbr.factory_reset()
    assert aioclient_mock.call_count == 1


async def test_get_active_dataset_camel(aioclient_mock: AiohttpClientMocker) -> None:
    """Dataset read returns camelCase and round-trips cleanly."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.CAMEL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", json=DATASET_JSON_CAMEL)

    dataset = await otbr.get_active_dataset()
    assert dataset is not None
    assert dataset.as_json() == DATASET_JSON_CAMEL


async def test_camel_read_with_pascal_straggler(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """CAMEL_CASE reads are always normalized, so Sept-2025..Apr-2026 OTBR
    builds that still emit pascal-case stragglers (e.g. `Routers`) parse
    cleanly instead of blowing up schema validation."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.CAMEL_CASE
    )

    straggler_dataset = {
        **DATASET_JSON_CAMEL,
        "securityPolicy": {
            **{
                k: v
                for k, v in DATASET_JSON_CAMEL["securityPolicy"].items()
                if k != "routers"
            },
            "Routers": DATASET_JSON_CAMEL["securityPolicy"]["routers"],
        },
    }
    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", json=straggler_dataset)

    dataset = await otbr.get_active_dataset()
    assert dataset is not None
    assert dataset.security_policy is not None
    assert dataset.security_policy.routers is True
    assert dataset.as_json() == DATASET_JSON_CAMEL


async def test_create_active_dataset_camel_wire(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """In CAMEL_CASE mode the wire body is camelCase."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.CAMEL_CASE
    )

    aioclient_mock.put(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CREATED)

    await otbr.create_active_dataset(
        python_otbr_api.ActiveDataSet(network_name="OpenThread HA", channel=15)
    )
    assert aioclient_mock.mock_calls[-1][2] == {
        "networkName": "OpenThread HA",
        "channel": 15,
    }
