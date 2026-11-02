"""Tests for the /.well-known/thread/br-rest API discovery endpoint."""

from http import HTTPStatus

import pytest
import python_otbr_api

from tests.test_util.aiohttp import AiohttpClientMocker

BASE_URL = "http://core-openthread-border-router:8081"

WELL_KNOWN_JSON = {
    "api": {"version": "0.3.0", "base": "/api/"},
    "links": [
        {
            "href": "/.well-known/thread/br-rest",
            "rel": "self",
            "type": ["application/json"],
        },
        {"href": "/api/node", "rel": "node", "type": ["application/vnd.api+json"]},
        {"href": "/api/actions", "rel": "task", "type": ["application/vnd.api+json"]},
        {
            "href": "/api/devices",
            "rel": "device",
            "type": ["application/vnd.api+json"],
        },
        {
            "href": "/api/diagnostics",
            "rel": "diagnostic",
            "type": ["application/vnd.api+json"],
        },
    ],
}


def _otbr(aioclient_mock: AiohttpClientMocker) -> python_otbr_api.OTBR:
    return python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())


async def test_get_api_version(aioclient_mock: AiohttpClientMocker) -> None:
    """A 200 with a version resource returns the advertised semver string."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/.well-known/thread/br-rest", json=WELL_KNOWN_JSON)

    assert await otbr.get_api_version() == "0.3.0"


async def test_get_api_version_not_supported(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 404 means the router predates ot-br-posix #3330: version is unknown."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(
        f"{BASE_URL}/.well-known/thread/br-rest", status=HTTPStatus.NOT_FOUND
    )

    assert await otbr.get_api_version() is None


async def test_get_api_version_unexpected_status(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Any other non-200 status raises OTBRError."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(
        f"{BASE_URL}/.well-known/thread/br-rest",
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_api_version()


async def test_get_api_version_malformed_body(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 200 without the expected `api.version` field raises OTBRError."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/.well-known/thread/br-rest", json={"api": {}})

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_api_version()


async def test_get_api_version_runs_once(aioclient_mock: AiohttpClientMocker) -> None:
    """Detection happens lazily on first call and is cached for subsequent calls."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/.well-known/thread/br-rest", json=WELL_KNOWN_JSON)

    assert await otbr.get_api_version() == "0.3.0"
    assert await otbr.get_api_version() == "0.3.0"

    assert aioclient_mock.call_count == 1


async def test_get_api_version_not_supported_runs_once(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 404 result is cached too, so repeated calls don't re-probe."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(
        f"{BASE_URL}/.well-known/thread/br-rest", status=HTTPStatus.NOT_FOUND
    )

    assert await otbr.get_api_version() is None
    assert await otbr.get_api_version() is None

    assert aioclient_mock.call_count == 1


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("0.5.9", False),
        ("0.6.0", True),
        ("0.6", True),
        ("0.10.1", True),
        ("1.0.0-rc1", True),
    ],
)
async def test_registers_pending_dataset_with_leader(
    aioclient_mock: AiohttpClientMocker, version: str, expected: bool
) -> None:
    """Routers register pending datasets with the leader from API 0.6.0."""
    aioclient_mock.get(
        f"{BASE_URL}/.well-known/thread/br-rest",
        json=WELL_KNOWN_JSON | {"api": {"version": version, "base": "/api/"}},
    )
    otbr = _otbr(aioclient_mock)
    assert await otbr.registers_pending_dataset_with_leader() is expected


async def test_registers_pending_dataset_with_leader_without_api_version(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A router without the discovery endpoint writes pending datasets itself."""
    aioclient_mock.get(
        f"{BASE_URL}/.well-known/thread/br-rest", status=HTTPStatus.NOT_FOUND
    )
    otbr = _otbr(aioclient_mock)
    assert await otbr.registers_pending_dataset_with_leader() is False


async def test_registers_pending_dataset_with_leader_unparsable_version(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An API version that cannot be parsed is an error."""
    aioclient_mock.get(
        f"{BASE_URL}/.well-known/thread/br-rest",
        json=WELL_KNOWN_JSON | {"api": {"version": "unknown", "base": "/api/"}},
    )
    with pytest.raises(python_otbr_api.OTBRError):
        await _otbr(aioclient_mock).registers_pending_dataset_with_leader()
