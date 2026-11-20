"""Test the OTBR REST API client with an older OTBR instance."""

from http import HTTPStatus
from typing import Any

import pytest
import python_otbr_api
from python_otbr_api import KeyFormat, tlv_parser

from tests.test_util.aiohttp import AiohttpClientMocker

BASE_URL = "http://core-silabs-multiprotocol:8081"
DATASET_JSON: dict[str, Any] = {
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
DATASET_TLVS = bytes.fromhex(
    "0E080000000000010000000300000F35060004001FFFE0020811111111222222220708FDAD"
    "70BFE5AA15DD051000112233445566778899AABBCCDDEEFF030E4F70656E54687265616444"
    "656D6F010212340410445F2B5CA6F2A93A55CE570A70EFEECB0C0402A0F7F8"
)


def _sent_pending(
    aioclient_mock: AiohttpClientMocker,
) -> dict[tlv_parser.MeshcopTLVType | int, tlv_parser.MeshcopTLVItem]:
    """Return the pending dataset the last request wrote."""
    method, url, data, _ = aioclient_mock.mock_calls[-1]
    assert (method, url.path) == ("PUT", "/node/dataset/pending")
    return tlv_parser.parse_tlv(data)


async def test_factory_reset(aioclient_mock: AiohttpClientMocker) -> None:
    """Test factory_reset."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(f"{BASE_URL}/node", status=HTTPStatus.OK)

    await otbr.factory_reset()
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[-1][0] == "DELETE"
    assert aioclient_mock.mock_calls[-1][1].path == "/node"
    assert aioclient_mock.mock_calls[-1][2] is None


async def test_factory_reset_unsupported(aioclient_mock: AiohttpClientMocker) -> None:
    """Test factory_reset is unsupported."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(f"{BASE_URL}/node", status=HTTPStatus.METHOD_NOT_ALLOWED)

    with pytest.raises(python_otbr_api.FactoryResetNotSupportedError):
        await otbr.factory_reset()


async def test_factory_reset_201(aioclient_mock: AiohttpClientMocker) -> None:
    """Test factory_reset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(f"{BASE_URL}/node", status=HTTPStatus.CREATED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.factory_reset()


async def test_get_border_agent_id(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_border_agent_id."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    mock_response = "230C6A1AC57F6F4BE262ACF32E5EF52C"

    aioclient_mock.get(f"{BASE_URL}/node/ba-id", json=mock_response)

    assert await otbr.get_border_agent_id() == bytes.fromhex(mock_response)


async def test_get_border_agent_id_unsupported(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test get_border_agent_id with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/ba-id", status=HTTPStatus.NOT_FOUND)

    with pytest.raises(python_otbr_api.GetBorderAgentIdNotSupportedError):
        await otbr.get_border_agent_id()


async def test_get_border_agent_id_invalid(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_border_agent_id with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/ba-id", text="unexpected")

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_border_agent_id()


async def test_get_border_agent_id_201(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_border_agent_id with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/ba-id", status=HTTPStatus.CREATED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_border_agent_id()


async def test_set_enabled(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_enabled."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.put(f"{BASE_URL}/node/state", status=HTTPStatus.OK)

    await otbr.set_enabled(True)
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/state"
    assert aioclient_mock.mock_calls[-1][2] == "enable"

    await otbr.set_enabled(False)
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/state"
    assert aioclient_mock.mock_calls[-1][2] == "disable"


async def test_get_active_dataset(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", json=DATASET_JSON)

    active_timestamp = python_otbr_api.models.Timestamp(
        DATASET_JSON["ActiveTimestamp"]["Authoritative"],
        DATASET_JSON["ActiveTimestamp"]["Seconds"],
        DATASET_JSON["ActiveTimestamp"]["Ticks"],
    )
    security_policy = python_otbr_api.models.SecurityPolicy(
        DATASET_JSON["SecurityPolicy"]["AutonomousEnrollment"],
        DATASET_JSON["SecurityPolicy"]["CommercialCommissioning"],
        DATASET_JSON["SecurityPolicy"]["ExternalCommissioning"],
        DATASET_JSON["SecurityPolicy"]["NativeCommissioning"],
        DATASET_JSON["SecurityPolicy"]["NetworkKeyProvisioning"],
        DATASET_JSON["SecurityPolicy"]["NonCcmRouters"],
        DATASET_JSON["SecurityPolicy"]["ObtainNetworkKey"],
        DATASET_JSON["SecurityPolicy"]["RotationTime"],
        DATASET_JSON["SecurityPolicy"]["Routers"],
        DATASET_JSON["SecurityPolicy"]["TobleLink"],
    )

    active_dataset = await otbr.get_active_dataset()
    assert active_dataset == python_otbr_api.ActiveDataSet(
        active_timestamp,
        DATASET_JSON["ChannelMask"],
        DATASET_JSON["Channel"],
        DATASET_JSON["ExtPanId"],
        DATASET_JSON["MeshLocalPrefix"],
        DATASET_JSON["NetworkKey"],
        DATASET_JSON["NetworkName"],
        DATASET_JSON["PanId"],
        DATASET_JSON["PSKc"],
        security_policy,
    )


async def test_get_active_dataset_empty(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.NO_CONTENT)
    assert await otbr.get_active_dataset() is None


async def test_get_active_dataset_tlvs(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_active_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    mock_response = (
        "0E080000000000010000000300001035060004001FFFE00208F642646DA209B1C00708FDF57B5A"
        "0FE2AAF60510DE98B5BA1A528FEE049D4B4B01835375030D4F70656E5468726561642048410102"
        "25A40410F5DD18371BFD29E1A601EF6FFAD94C030C0402A0F7F8"
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text=mock_response)

    assert await otbr.get_active_dataset_tlvs() == bytes.fromhex(mock_response)


async def test_get_active_dataset_tlvs_empty(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.NO_CONTENT)
    assert await otbr.get_active_dataset_tlvs() is None


async def test_get_pending_dataset_tlvs(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_pending_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    mock_response = (
        "0E080000000000010000340400006699000300000C35060004001FFFE00208057B7CD3D6CC9F65"
        "0708FD17C9D59809B27A05107546326F20BCCFD946609FBAF7F39AD5030F4F70656E5468726561"
        "642D32366363010226CC0410FA7EC34EBE58DD1FD74F13F65D021C5B0C0402A0F7F8"
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", text=mock_response)

    assert await otbr.get_pending_dataset_tlvs() == bytes.fromhex(mock_response)


async def test_get_pending_dataset_tlvs_empty(aioclient_mock: AiohttpClientMocker):
    """Test get_pending_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    assert await otbr.get_pending_dataset_tlvs() is None


async def test_create_active_dataset(aioclient_mock: AiohttpClientMocker):
    """Test create_active_dataset."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.put(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CREATED)

    await otbr.create_active_dataset(python_otbr_api.ActiveDataSet())
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/active"
    assert aioclient_mock.mock_calls[-1][2] == {}

    await otbr.create_active_dataset(
        python_otbr_api.ActiveDataSet(network_name="OpenThread HA")
    )
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/active"
    assert aioclient_mock.mock_calls[-1][2] == {"NetworkName": "OpenThread HA"}

    await otbr.create_active_dataset(
        python_otbr_api.ActiveDataSet(network_name="OpenThread HA", channel=15)
    )
    assert aioclient_mock.call_count == 3
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/active"
    assert aioclient_mock.mock_calls[-1][2] == {
        "NetworkName": "OpenThread HA",
        "Channel": 15,
    }


async def test_delete_active_dataset(aioclient_mock: AiohttpClientMocker):
    """Test delete_active_dataset."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.OK)

    await otbr.delete_active_dataset()
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[-1][0] == "DELETE"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/active"
    assert aioclient_mock.mock_calls[-1][2] is None


async def test_create_pending_dataset(aioclient_mock: AiohttpClientMocker):
    """Test create_pending_dataset."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CREATED)

    await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/pending"
    assert aioclient_mock.mock_calls[-1][2] == {}
    assert aioclient_mock.mock_calls[-1][3]["If-None-Match"] == "*"

    await otbr.create_pending_dataset(
        python_otbr_api.PendingDataSet(
            python_otbr_api.ActiveDataSet(network_name="OpenThread HA"),
            12345,
            python_otbr_api.Timestamp(),
        )
    )
    assert aioclient_mock.call_count == 4
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/pending"
    assert aioclient_mock.mock_calls[-1][2] == {
        "ActiveDataset": {
            "NetworkName": "OpenThread HA",
        },
        "Delay": 12345,
        "PendingTimestamp": {},
    }

    await otbr.create_pending_dataset(
        python_otbr_api.PendingDataSet(
            python_otbr_api.ActiveDataSet(network_name="OpenThread HA", channel=15),
            23456,
        )
    )
    assert aioclient_mock.call_count == 6
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/pending"
    assert aioclient_mock.mock_calls[-1][2] == {
        "ActiveDataset": {
            "Channel": 15,
            "NetworkName": "OpenThread HA",
        },
        "Delay": 23456,
    }


async def test_delete_pending_dataset(aioclient_mock: AiohttpClientMocker):
    """Test delete_pending_dataset."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.OK)

    await otbr.delete_pending_dataset()
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[-1][0] == "DELETE"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/pending"
    assert aioclient_mock.mock_calls[-1][2] is None


async def test_set_channel(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_channel."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text=DATASET_TLVS.hex())
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CREATED)

    await otbr.set_channel(16, 1234)

    assert aioclient_mock.call_count == 3
    sent = _sent_pending(aioclient_mock)
    channel = sent[tlv_parser.MeshcopTLVType.CHANNEL]
    assert isinstance(channel, tlv_parser.Channel)
    assert channel.channel == 16
    stamp = sent[tlv_parser.MeshcopTLVType.ACTIVETIMESTAMP]
    assert isinstance(stamp, tlv_parser.Timestamp)
    assert stamp.seconds == 2
    delay = sent[tlv_parser.MeshcopTLVType.DELAYTIMER]
    assert isinstance(delay, tlv_parser.DelayTimer)
    assert delay.delay == 1234


async def test_set_channel_default_delay(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_channel."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text=DATASET_TLVS.hex())
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CREATED)

    await otbr.set_channel(16)

    delay = _sent_pending(aioclient_mock)[tlv_parser.MeshcopTLVType.DELAYTIMER]
    assert isinstance(delay, tlv_parser.DelayTimer)
    assert delay.delay == 300000


async def test_set_channel_no_timestamp(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_channel."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    active = tlv_parser.parse_tlv(DATASET_TLVS.hex())
    del active[tlv_parser.MeshcopTLVType.ACTIVETIMESTAMP]
    aioclient_mock.get(
        f"{BASE_URL}/node/dataset/active", text=tlv_parser.encode_tlv(active)
    )
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CREATED)

    await otbr.set_channel(16)

    stamp = _sent_pending(aioclient_mock)[tlv_parser.MeshcopTLVType.ACTIVETIMESTAMP]
    assert isinstance(stamp, tlv_parser.Timestamp)
    assert stamp.seconds == 1


async def test_set_channel_keeps_unmodelled_tlvs(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """TLVs the JSON model lacks, such as the wake-up channel, are kept."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    active = DATASET_TLVS + bytes.fromhex("4a0300000f")
    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text=active.hex())
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CREATED)

    await otbr.set_channel(16)

    wakeup = _sent_pending(aioclient_mock)[tlv_parser.MeshcopTLVType.WAKEUP_CHANNEL]
    assert wakeup.data == bytes.fromhex("00000f")


async def test_set_channel_malformed_dataset(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A malformed active dataset is an error, and nothing is written."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text="0e08")

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_channel(16)
    assert not [call for call in aioclient_mock.mock_calls if call[0] == "PUT"]


async def test_set_channel_invalid_channel(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_channel."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_channel(123)


async def test_set_channel_no_dataset(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_channel."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.NO_CONTENT)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_channel(16)


async def test_set_channel_rejected_while_pending(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A channel change is refused while a pending dataset is in place."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    mock_response = (
        "0E080000000000010000340400006699000300000C35060004001FFFE00208057B7CD3D6CC9F65"
        "0708FD17C9D59809B27A05107546326F20BCCFD946609FBAF7F39AD5030F4F70656E5468726561"
        "642D32366363010226CC0410FA7EC34EBE58DD1FD74F13F65D021C5B0C0402A0F7F8"
    )
    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text=DATASET_TLVS.hex())
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", text=mock_response)

    with pytest.raises(python_otbr_api.PendingDatasetConflictError):
        await otbr.set_channel(16)
    assert not [call for call in aioclient_mock.mock_calls if call[0] == "PUT"]
    assert aioclient_mock.call_count == 2


async def test_get_extended_address(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_active_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    mock_response = "4EF6C4F3FF750626"

    aioclient_mock.get(f"{BASE_URL}/node/ext-address", json=mock_response)

    assert await otbr.get_extended_address() == bytes.fromhex(mock_response)


async def test_get_coprocessor_version(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_coprocessor_version."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    mock_response = (
        "OPENTHREAD/thread-reference-20200818-1740-g33cc75ed3;"
        " NRF52840; Jun 2 2022 14:25:49"
    )

    aioclient_mock.get(f"{BASE_URL}/node/coprocessor/version", json=mock_response)

    assert await otbr.get_coprocessor_version() == mock_response


async def test_set_enabled_201(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_enabled."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.put(f"{BASE_URL}/node/state", status=HTTPStatus.CREATED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_enabled(True)


async def test_get_active_dataset_201(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CREATED)
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_active_dataset()


async def test_get_active_dataset_invalid(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text="unexpected")
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_active_dataset()


async def test_get_active_dataset_tlvs_201(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset_tlvs with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CREATED)
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_active_dataset_tlvs()


async def test_get_active_dataset_tlvs_invalid(aioclient_mock: AiohttpClientMocker):
    """Test get_active_dataset_tlvs with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/active", text="unexpected")
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_active_dataset_tlvs()


async def test_get_pending_dataset_tlvs_201(aioclient_mock: AiohttpClientMocker):
    """Test test_get_pending_dataset_tlvs_201 with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CREATED)
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_pending_dataset_tlvs()


async def test_test_get_pending_dataset_tlvs_201_invalid(
    aioclient_mock: AiohttpClientMocker,
):
    """Test get_pending_dataset_tlvs with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", text="unexpected")
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_pending_dataset_tlvs()


async def test_create_active_dataset_thread_active(aioclient_mock: AiohttpClientMocker):
    """Test create_active_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.put(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CONFLICT)

    with pytest.raises(python_otbr_api.ThreadNetworkActiveError):
        await otbr.create_active_dataset(python_otbr_api.ActiveDataSet())


async def test_create_active_dataset_202(aioclient_mock: AiohttpClientMocker):
    """Test create_active_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.put(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.ACCEPTED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.create_active_dataset(python_otbr_api.ActiveDataSet())


async def test_delete_active_dataset_thread_active(aioclient_mock: AiohttpClientMocker):
    """Test delete_active_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CONFLICT)

    with pytest.raises(python_otbr_api.ThreadNetworkActiveError):
        await otbr.delete_active_dataset()


async def test_delete_active_dataset_202(aioclient_mock: AiohttpClientMocker):
    """Test delete_active_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.ACCEPTED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.delete_active_dataset()


async def test_create_pending_dataset_rejected(
    aioclient_mock: AiohttpClientMocker,
):
    """Test create_pending_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(
        f"{BASE_URL}/node/dataset/pending",
        status=HTTPStatus.CONFLICT,
        json={"title": "Conflict", "status": 409, "detail": "rejected by leader"},
    )

    with pytest.raises(python_otbr_api.PendingDatasetRejectedError) as exc_info:
        await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())
    # The reason is the detail; the title is only the HTTP status phrase.
    assert exc_info.value.reason == "rejected by leader"
    assert "rejected by leader" in str(exc_info.value)
    assert "Conflict" not in str(exc_info.value)


async def test_create_pending_dataset_202(aioclient_mock: AiohttpClientMocker):
    """Test create_pending_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.ACCEPTED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())


async def test_delete_pending_dataset_thread_active(
    aioclient_mock: AiohttpClientMocker,
):
    """Test delete_pending_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(
        f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CONFLICT
    )

    with pytest.raises(python_otbr_api.ThreadNetworkActiveError):
        await otbr.delete_pending_dataset()


async def test_delete_pending_dataset_202(aioclient_mock: AiohttpClientMocker):
    """Test delete_pending_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.delete(
        f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.ACCEPTED
    )

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.delete_pending_dataset()


async def test_set_active_dataset_tlvs_thread_active(
    aioclient_mock: AiohttpClientMocker,
):
    """Test set_active_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.put(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.CONFLICT)

    with pytest.raises(python_otbr_api.ThreadNetworkActiveError):
        await otbr.set_active_dataset_tlvs(b"")


async def test_set_active_dataset_tlvs_202(aioclient_mock: AiohttpClientMocker):
    """Test set_active_dataset with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.put(f"{BASE_URL}/node/dataset/active", status=HTTPStatus.ACCEPTED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_active_dataset_tlvs(b"")


async def test_get_extended_address_201(aioclient_mock: AiohttpClientMocker) -> None:
    """Test get_extended_address with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/ext-address", status=HTTPStatus.CREATED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_extended_address()


async def test_get_extended_address_invalid(aioclient_mock: AiohttpClientMocker):
    """Test get_extended_address with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/ext-address", text="unexpected")
    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_extended_address()


async def test_get_coprocessor_version_invalid(aioclient_mock: AiohttpClientMocker):
    """Test get_coprocessor_version with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(
        f"{BASE_URL}/node/coprocessor/version", status=HTTPStatus.NOT_FOUND
    )

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.get_coprocessor_version()


async def test_set_pending_dataset_tlvs(aioclient_mock: AiohttpClientMocker) -> None:
    """Test set_pending_dataset_tlvs."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    dataset = bytes.fromhex(
        "0E080000000000010000000300000F35060004001FFFE0020811111111222222220708FDAD"
        "70BFE5AA15DD051000112233445566778899AABBCCDDEEFF030E4F70656E54687265616444"
        "656D6F010212340410445F2B5CA6F2A93A55CE570A70EFEECB0C0402A0F7F8"
    )
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CREATED)

    await otbr.set_pending_dataset_tlvs(dataset)
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[-1][0] == "PUT"
    assert aioclient_mock.mock_calls[-1][1].path == "/node/dataset/pending"
    assert aioclient_mock.mock_calls[-1][2] == dataset.hex()
    assert aioclient_mock.mock_calls[-1][3]["If-None-Match"] == "*"


async def test_set_pending_dataset_tlvs_rejected(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test set_pending_dataset_tlvs with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(
        f"{BASE_URL}/node/dataset/pending",
        status=HTTPStatus.CONFLICT,
        text="rejected by leader",
    )

    with pytest.raises(python_otbr_api.PendingDatasetRejectedError) as exc_info:
        await otbr.set_pending_dataset_tlvs(b"")
    # A plain body is taken as it is.
    assert exc_info.value.reason == "rejected by leader"


async def test_set_pending_dataset_tlvs_refused_while_pending(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a write is refused while a pending dataset is in place."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    in_flight = "0E080000000000010000340400006699000300000C"
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", text=in_flight)

    with pytest.raises(python_otbr_api.PendingDatasetConflictError):
        await otbr.set_pending_dataset_tlvs(bytes.fromhex(in_flight))
    assert aioclient_mock.call_count == 1


async def test_set_pending_dataset_tlvs_refused_by_router(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the border router refusing the precondition is surfaced."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(
        f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.PRECONDITION_FAILED
    )

    # The dedicated type, so a caller can tell "nothing was written because a
    # dataset is in place" from a transport or protocol failure.
    with pytest.raises(python_otbr_api.PendingDatasetConflictError):
        await otbr.set_pending_dataset_tlvs(b"")


async def test_set_pending_dataset_tlvs_202(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test set_pending_dataset_tlvs with error."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.ACCEPTED)

    with pytest.raises(python_otbr_api.OTBRError):
        await otbr.set_pending_dataset_tlvs(b"")


async def test_create_pending_dataset_refused_while_pending(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a write is refused while a pending dataset is in place."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    in_flight = "0E080000000000010000340400006699000300000C"
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", text=in_flight)

    with pytest.raises(python_otbr_api.PendingDatasetConflictError):
        await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())
    assert aioclient_mock.call_count == 1


async def test_create_pending_dataset_refused_by_router(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the border router refusing the precondition is surfaced.

    A pending dataset created between the local check and the write is only
    caught by the router, which evaluates If-None-Match atomically with it.
    """
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(
        f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.PRECONDITION_FAILED
    )

    with pytest.raises(python_otbr_api.PendingDatasetConflictError):
        await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())
