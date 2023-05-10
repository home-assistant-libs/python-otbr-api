"""Test the OTBR REST API client."""

from http import HTTPStatus

import pytest
import python_otbr_api

from tests.test_util.aiohttp import AiohttpClientMocker

BASE_URL = "http://core-silabs-multiprotocol:8081"
DATASET_JSON = {
    "ActiveTimestamp": {
        "Authoritative": False,
        "Seconds": 1,
        "Ticks": 0,
    },
    "ChannelMask": 134215680,
    "Channel": 15,
    "ExtPanId": "8478E3379E047B92",
    "MeshLocalPrefix": "fd89:bde7:42ed:a901::/64",
    "NetworkKey": "96271D6ECC78749114AB6A591E0D06F1",
    "NetworkName": "OpenThread HA",
    "PanId": 33991,
    "PSKc": "9760C89414D461AC717DCD105EB87E5B",
    "SecurityPolicy": {
        "AutonomousEnrollment": False,
        "CommercialCommissioning": False,
        "ExternalCommissioning": True,
        "NativeCommissioning": True,
        "NetworkKeyProvisioning": False,
        "NonCcmRouters": False,
        "ObtainNetworkKey": True,
        "RotationTime": 672,
        "Routers": True,
        "TobleLink": True,
    },
}


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


async def test_get_active_dataset(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    mock_response = DATASET_JSON

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", json=DATASET_JSON)

    active_timestamp = python_otbr_api.models.Timestamp(
        mock_response["ActiveTimestamp"]["Authoritative"],
        mock_response["ActiveTimestamp"]["Seconds"],
        mock_response["ActiveTimestamp"]["Ticks"],
    )
    security_policy = python_otbr_api.models.SecurityPolicy(
        mock_response["SecurityPolicy"]["AutonomousEnrollment"],
        mock_response["SecurityPolicy"]["CommercialCommissioning"],
        mock_response["SecurityPolicy"]["ExternalCommissioning"],
        mock_response["SecurityPolicy"]["NativeCommissioning"],
        mock_response["SecurityPolicy"]["NetworkKeyProvisioning"],
        mock_response["SecurityPolicy"]["NonCcmRouters"],
        mock_response["SecurityPolicy"]["ObtainNetworkKey"],
        mock_response["SecurityPolicy"]["RotationTime"],
        mock_response["SecurityPolicy"]["Routers"],
        mock_response["SecurityPolicy"]["TobleLink"],
    )

    active_dataset = await otbr.get_active_dataset()
    assert active_dataset == python_otbr_api.OperationalDataSet(
        active_timestamp,
        mock_response["ChannelMask"],
        mock_response["Channel"],
        None,  # delay
        mock_response["ExtPanId"],
        mock_response["MeshLocalPrefix"],
        mock_response["NetworkKey"],
        mock_response["NetworkName"],
        mock_response["PanId"],
        None,  # pending_timestamp
        mock_response["PSKc"],
        security_policy,
    )
    assert active_dataset.as_json() == mock_response


async def test_get_active_dataset_empty(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.NO_CONTENT)
    assert await otbr.get_active_dataset() is None


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


@pytest.mark.parametrize("dataset_type", ["active", "pending"])
async def test_create_active_pending_dataset(
    aioclient_mock: AiohttpClientMocker, dataset_type: str
):
    """Test create_active_dataset + create_pending_dataset."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.post(
        f"{BASE_URL}/node/dataset/{dataset_type}", status=HTTPStatus.ACCEPTED
    )

    await getattr(otbr, f"create_{dataset_type}_dataset")(
        python_otbr_api.OperationalDataSet()
    )
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[-1][0] == "POST"
    assert aioclient_mock.mock_calls[-1][1].path == f"/node/dataset/{dataset_type}"
    assert aioclient_mock.mock_calls[-1][2] == {}

    await getattr(otbr, f"create_{dataset_type}_dataset")(
        python_otbr_api.OperationalDataSet(network_name="OpenThread HA")
    )
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[-1][0] == "POST"
    assert aioclient_mock.mock_calls[-1][1].path == f"/node/dataset/{dataset_type}"
    assert aioclient_mock.mock_calls[-1][2] == {"NetworkName": "OpenThread HA"}

    await getattr(otbr, f"create_{dataset_type}_dataset")(
        python_otbr_api.OperationalDataSet(network_name="OpenThread HA", channel=15)
    )
    assert aioclient_mock.call_count == 3
    assert aioclient_mock.mock_calls[-1][0] == "POST"
    assert aioclient_mock.mock_calls[-1][1].path == f"/node/dataset/{dataset_type}"
    assert aioclient_mock.mock_calls[-1][2] == {
        "NetworkName": "OpenThread HA",
        "Channel": 15,
    }


async def test_set_channel(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_channel."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", json=DATASET_JSON)
    aioclient_mock.post(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.ACCEPTED)
    new_channel = 16
    expected_active_timestamp = DATASET_JSON["ActiveTimestamp"] | {"Seconds": 2}
    expected_pending_dataset = DATASET_JSON | {
        "ActiveTimestamp": expected_active_timestamp,
        "Channel": new_channel,
        "Delay": 300000,
    }

    assert new_channel != DATASET_JSON["Channel"]
    await otbr.set_channel(new_channel)
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[0][0] == "GET"
    assert aioclient_mock.mock_calls[0][1].path == "/node/dataset/active"
    assert aioclient_mock.mock_calls[1][0] == "POST"
    assert aioclient_mock.mock_calls[1][1].path == "/node/dataset/pending"
    assert aioclient_mock.mock_calls[1][2] == expected_pending_dataset


async def test_set_channel_invalid_channel(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_channel."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_channel(123)


async def test_set_channel_no_dataset(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_channel."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.NO_CONTENT)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_channel(16)


async def test_get_extended_address(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_active_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    mock_response = "4EF6C4F3FF750626"

    aioclient_mock.get(f"{BASE_URL}/node/ext-address", json=mock_response)

    assert await otbr.get_extended_address() == bytes.fromhex(mock_response)


async def test_set_enabled_201(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_enabled."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.post(f"{BASE_URL}/node/state", status=HTTPStatus.CREATED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_enabled(True)


async def test_get_active_dataset_201(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CREATED)
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_active_dataset()


async def test_get_active_dataset_invalid(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text="unexpected")
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_active_dataset()


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


@pytest.mark.parametrize("dataset_type", ["active", "pending"])
async def test_create_active_pending_dataset_200(
    aioclient_mock: AiohttpClientMocker, dataset_type: str
):
    """Test create_active_dataset + create_pending_dataset with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.post(f"{BASE_URL}/node/dataset/{dataset_type}", status=HTTPStatus.OK)

    with pytest.raises(python_otbr_api.OTBRError):
        await getattr(otbr, f"create_{dataset_type}_dataset")(
            python_otbr_api.OperationalDataSet()
        )


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


async def test_get_extended_address_201(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_extended_address with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/ext-address", status=HTTPStatus.CREATED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_extended_address()


async def test_get_extended_address_invalid(aioclient_mock: AiohttpClientMocker):
    """Test get_extended_address with error."""
    otbr = python_otbr_api.OTBR(BASE_URL, aioclient_mock.create_session())

    aioclient_mock.get(f"{BASE_URL}/node/ext-address", text="unexpected")
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_extended_address()
