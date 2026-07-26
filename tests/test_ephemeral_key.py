"""Tests for the ephemeral key (ePSKc) REST API."""

from http import HTTPStatus

import pytest
import python_otbr_api
from python_otbr_api import EphemeralKeyState, KeyFormat

from tests.test_util.aiohttp import AiohttpClientMocker

BASE_URL = "http://core-openthread-border-router:8081"


def _otbr(aioclient_mock: AiohttpClientMocker) -> python_otbr_api.OTBR:
    return python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.CAMEL_CASE
    )


async def test_get_ephemeral_key_enabled_true(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 200 with body "enabled" reports the feature as enabled."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/node/ba-epskc/state", json="enabled")

    assert await otbr.get_ephemeral_key_enabled() is True


async def test_get_ephemeral_key_enabled_false(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 200 with body "disabled" reports the feature as disabled."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/node/ba-epskc/state", json="disabled")

    assert await otbr.get_ephemeral_key_enabled() is False


async def test_get_ephemeral_key_enabled_not_supported(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 404 means the router does not support ePSKc."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/node/ba-epskc/state", status=HTTPStatus.NOT_FOUND)

    with pytest.raises(python_otbr_api.EphemeralKeyNotSupportedError):
        await otbr.get_ephemeral_key_enabled()


async def test_get_ephemeral_key_enabled_unexpected_status(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Any other non-200 status raises OTBRError."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(
        f"{BASE_URL}/node/ba-epskc/state", status=HTTPStatus.INTERNAL_SERVER_ERROR
    )

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_ephemeral_key_enabled()


async def test_set_ephemeral_key_enabled(aioclient_mock: AiohttpClientMocker) -> None:
    """Enabling sends body "enable", disabling sends body "disable"."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.put(f"{BASE_URL}/node/ba-epskc/state", status=HTTPStatus.OK)

    await otbr.set_ephemeral_key_enabled(True)
    assert aioclient_mock.mock_calls[-1][2] == "enable"

    await otbr.set_ephemeral_key_enabled(False)
    assert aioclient_mock.mock_calls[-1][2] == "disable"


async def test_set_ephemeral_key_enabled_not_supported(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 404 means the router does not support ePSKc."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.put(f"{BASE_URL}/node/ba-epskc/state", status=HTTPStatus.NOT_FOUND)

    with pytest.raises(python_otbr_api.EphemeralKeyNotSupportedError):
        await otbr.set_ephemeral_key_enabled(True)


async def test_get_ephemeral_key_status(aioclient_mock: AiohttpClientMocker) -> None:
    """A successful status response is parsed into an EphemeralKeyStatus."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(
        f"{BASE_URL}/node/ba-epskc/key", json={"state": "started", "port": 49152}
    )

    status = await otbr.get_ephemeral_key_status()
    assert status.state == EphemeralKeyState.STARTED
    assert status.port == 49152


async def test_get_ephemeral_key_status_not_supported(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 404 means the router does not support ePSKc."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/node/ba-epskc/key", status=HTTPStatus.NOT_FOUND)

    with pytest.raises(python_otbr_api.EphemeralKeyNotSupportedError):
        await otbr.get_ephemeral_key_status()


async def test_get_ephemeral_key_status_invalid(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A malformed response body raises OTBRError."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/node/ba-epskc/key", json={"state": "started"})

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_ephemeral_key_status()


async def test_activate_ephemeral_key_defaults(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """With no arguments an empty JSON object is posted."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.post(
        f"{BASE_URL}/node/ba-epskc/key",
        json={"tap": "123456789", "port": 49152},
    )

    result = await otbr.activate_ephemeral_key()
    assert result.tap == "123456789"
    assert result.port == 49152
    assert aioclient_mock.mock_calls[-1][2] == {}


async def test_activate_ephemeral_key_with_params(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """lifetime and port are forwarded in the request body when given."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.post(
        f"{BASE_URL}/node/ba-epskc/key",
        json={"tap": "123456789", "port": 12345},
    )

    await otbr.activate_ephemeral_key(lifetime=60000, port=12345)
    assert aioclient_mock.mock_calls[-1][2] == {"lifetime": 60000, "port": 12345}


async def test_activate_ephemeral_key_conflict(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 409 means the feature is disabled or a key is already active."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/node/ba-epskc/key", status=HTTPStatus.CONFLICT)

    with pytest.raises(python_otbr_api.EphemeralKeyConflictError):
        await otbr.activate_ephemeral_key()


async def test_activate_ephemeral_key_not_supported(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 404 means the router does not support ePSKc."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/node/ba-epskc/key", status=HTTPStatus.NOT_FOUND)

    with pytest.raises(python_otbr_api.EphemeralKeyNotSupportedError):
        await otbr.activate_ephemeral_key()


async def test_deactivate_ephemeral_key(aioclient_mock: AiohttpClientMocker) -> None:
    """A successful deactivation returns None."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.delete(f"{BASE_URL}/node/ba-epskc/key", status=HTTPStatus.OK)

    await otbr.deactivate_ephemeral_key()
    assert aioclient_mock.call_count == 1


async def test_deactivate_ephemeral_key_not_supported(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 404 means the router does not support ePSKc."""
    otbr = _otbr(aioclient_mock)
    aioclient_mock.delete(f"{BASE_URL}/node/ba-epskc/key", status=HTTPStatus.NOT_FOUND)

    with pytest.raises(python_otbr_api.EphemeralKeyNotSupportedError):
        await otbr.deactivate_ephemeral_key()
