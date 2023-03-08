"""Test the OTBR REST API client."""

from http import HTTPStatus

import pytest
import python_otbr_api

from tests.test_util.aiohttp import AiohttpClientMocker

BASE_URL = "http://core-silabs-multiprotocol:8081"


async def test_set_enabled(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_enabled."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.post(f"{BASE_URL}/node/state", status=HTTPStatus.OK)

    await otbr.set_enabled(True)
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[-1][0] == "POST"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/state"
    assert aioclient_mock.mock_calls[-1][2] == "enable"

    await otbr.set_enabled(False)
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[-1][0] == "POST"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/state"
    assert aioclient_mock.mock_calls[-1][2] == "disable"


async def test_get_active_dataset_tlvs(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_active_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    mock_response = (
        "0E080000000000010000000300001035060004001FFFE00208F642646DA209B1C00708FDF57B5A"
        "0FE2AAF60510DE98B5BA1A528FEE049D4B4B01835375030D4F70656E5468726561642048410102"
        "25A40410F5DD18371BFD29E1A601EF6FFAD94C030C0402A0F7F8"
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text=mock_response)

    assert await otbr.get_active_dataset_tlvs() == bytes.fromhex(mock_response)


async def test_get_active_dataset_tlvs_empty(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.NO_CONTENT)
    assert await otbr.get_active_dataset_tlvs() is None


async def test_create_active_dataset(aioclient_mock: AiohttpClientMocker):
    """Test create_active_dataset."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.post(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.ACCEPTED)

    await otbr.create_active_dataset(python_otbr_api.OperationalDataSet())
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[-1][0] == "POST"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/active"
    assert aioclient_mock.mock_calls[-1][2] == {}

    await otbr.create_active_dataset(
        python_otbr_api.OperationalDataSet(network_name="OpenThread HA")
    )
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[-1][0] == "POST"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/active"
    assert aioclient_mock.mock_calls[-1][2] == {"NetworkName": "OpenThread HA"}

    await otbr.create_active_dataset(
        python_otbr_api.OperationalDataSet(network_name="OpenThread HA", channel=15)
    )
    assert aioclient_mock.call_count == 3
    assert aioclient_mock.mock_calls[-1][0] == "POST"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/active"
    assert aioclient_mock.mock_calls[-1][2] == {
        "NetworkName": "OpenThread HA",
        "Channel": 15,
    }


async def test_set_enabled_201(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_enabled."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.post(f"{BASE_URL}/node/state", status=HTTPStatus.CREATED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_enabled(True)


async def test_get_active_dataset_tlvs_201(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset_tlvs with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CREATED)
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_active_dataset_tlvs()


async def test_get_active_dataset_tlvs_invalid(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset_tlvs with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text="unexpected")
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_active_dataset_tlvs()


async def test_create_active_dataset_thread_active(aioclient_mock: AiohttpClientMocker):
    """Test create_active_dataset with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.post(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CONFLICT)

    with pytest.raises(python_otbr_api.ThreadNetworkActiveError):
        await otbr.create_active_dataset(python_otbr_api.OperationalDataSet())


async def test_create_active_dataset_200(aioclient_mock: AiohttpClientMocker):
    """Test create_active_dataset with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.post(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.OK)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.create_active_dataset(python_otbr_api.OperationalDataSet())


async def test_set_active_dataset_tlvs_thread_active(
    aioclient_mock: AiohttpClientMocker,
):
    """Test set_active_dataset with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.put(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CONFLICT)

    with pytest.raises(python_otbr_api.ThreadNetworkActiveError):
        await otbr.set_active_dataset_tlvs(b"")


async def test_set_active_dataset_tlvs_200(aioclient_mock: AiohttpClientMocker):
    """Test set_active_dataset with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.put(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.OK)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_active_dataset_tlvs(b"")
