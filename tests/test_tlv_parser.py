"""Test the Thread TLV parser."""

import pytest

from python_otbr_api.tlv_parser import (
    Timestamp,
    Channel,
    MeshcopTLVItem,
    MeshcopTLVType,
    NetworkName,
    TLVError,
    encode_tlv,
    parse_tlv,
)


# Shared dataset covering the newly added Meshcop TLV types.
NEW_MESHCOP_DATASET = {
    MeshcopTLVType.DURATION: MeshcopTLVItem(
        MeshcopTLVType.DURATION, bytes.fromhex("05")
    ),
    MeshcopTLVType.PROVISIONING_URL: MeshcopTLVItem(
        MeshcopTLVType.PROVISIONING_URL, "test".encode()
    ),
    MeshcopTLVType.VENDOR_NAME_TLV: MeshcopTLVItem(
        MeshcopTLVType.VENDOR_NAME_TLV, "ACME".encode()
    ),
    MeshcopTLVType.UDP_ENCAPSULATION_TLV: MeshcopTLVItem(
        MeshcopTLVType.UDP_ENCAPSULATION_TLV, bytes.fromhex("beef")
    ),
    MeshcopTLVType.IPV6_ADDRESS_TLV: MeshcopTLVItem(
        MeshcopTLVType.IPV6_ADDRESS_TLV,
        bytes.fromhex("20010db8000000000000000000000001"),
    ),
    MeshcopTLVType.PENDINGTIMESTAMP: MeshcopTLVItem(
        MeshcopTLVType.PENDINGTIMESTAMP, bytes.fromhex("0000000000010000")
    ),
    MeshcopTLVType.DELAYTIMER: MeshcopTLVItem(
        MeshcopTLVType.DELAYTIMER, bytes.fromhex("00001388")
    ),
    MeshcopTLVType.COUNT: MeshcopTLVItem(MeshcopTLVType.COUNT, bytes.fromhex("03")),
    MeshcopTLVType.PERIOD: MeshcopTLVItem(MeshcopTLVType.PERIOD, bytes.fromhex("0032")),
    MeshcopTLVType.SCAN_DURATION: MeshcopTLVItem(
        MeshcopTLVType.SCAN_DURATION, bytes.fromhex("04")
    ),
    MeshcopTLVType.ENERGY_LIST: MeshcopTLVItem(
        MeshcopTLVType.ENERGY_LIST, bytes.fromhex("010203")
    ),
    MeshcopTLVType.THREAD_DOMAIN_NAME: MeshcopTLVItem(
        MeshcopTLVType.THREAD_DOMAIN_NAME, "home".encode()
    ),
    MeshcopTLVType.DISCOVERYREQUEST: MeshcopTLVItem(
        MeshcopTLVType.DISCOVERYREQUEST, bytes.fromhex("00")
    ),
    MeshcopTLVType.DISCOVERYRESPONSE: MeshcopTLVItem(
        MeshcopTLVType.DISCOVERYRESPONSE, bytes.fromhex("01")
    ),
    MeshcopTLVType.JOINERADVERTISEMENT: MeshcopTLVItem(
        MeshcopTLVType.JOINERADVERTISEMENT, bytes.fromhex("02")
    ),
}

# Expected TLV hex for NEW_MESHCOP_DATASET; order follows the dict insertion order.
NEW_MESHCOP_DATASET_HEX = (
    "170105200474657374210441434d453002beef311020010db8000000000000000000000001"
    "330800000000000100003404000013883601033702003238010439030102033b04686f6d65"
    "800100810101f10102"
)


def test_encode_tlv() -> None:
    """Test the TLV parser."""
    dataset = {
        MeshcopTLVType.ACTIVETIMESTAMP: MeshcopTLVItem(
            MeshcopTLVType.ACTIVETIMESTAMP, bytes.fromhex("0000000000010000")
        ),
        MeshcopTLVType.CHANNEL: MeshcopTLVItem(
            MeshcopTLVType.CHANNEL, bytes.fromhex("00000f")
        ),
        MeshcopTLVType.CHANNELMASK: MeshcopTLVItem(
            MeshcopTLVType.CHANNELMASK, bytes.fromhex("0004001fffe0")
        ),
        MeshcopTLVType.EXTPANID: MeshcopTLVItem(
            MeshcopTLVType.EXTPANID, bytes.fromhex("1111111122222222")
        ),
        MeshcopTLVType.MESHLOCALPREFIX: MeshcopTLVItem(
            MeshcopTLVType.MESHLOCALPREFIX, bytes.fromhex("fdad70bfe5aa15dd")
        ),
        MeshcopTLVType.NETWORKKEY: MeshcopTLVItem(
            MeshcopTLVType.NETWORKKEY, bytes.fromhex("00112233445566778899aabbccddeeff")
        ),
        MeshcopTLVType.NETWORKNAME: NetworkName(
            MeshcopTLVType.NETWORKNAME, "OpenThreadDemo".encode()
        ),
        MeshcopTLVType.PANID: MeshcopTLVItem(
            MeshcopTLVType.PANID, bytes.fromhex("1234")
        ),
        MeshcopTLVType.PSKC: MeshcopTLVItem(
            MeshcopTLVType.PSKC, bytes.fromhex("445f2b5ca6f2a93a55ce570a70efeecb")
        ),
        MeshcopTLVType.SECURITYPOLICY: MeshcopTLVItem(
            MeshcopTLVType.SECURITYPOLICY, bytes.fromhex("02a0f7f8")
        ),
    }
    dataset_tlv = encode_tlv(dataset)
    assert (
        dataset_tlv
        == (
            "0E080000000000010000000300000F35060004001FFFE0020811111111222222220708FDAD"
            "70BFE5AA15DD051000112233445566778899AABBCCDDEEFF030E4F70656E54687265616444"
            "656D6F010212340410445F2B5CA6F2A93A55CE570A70EFEECB0C0402A0F7F8"
        ).lower()
    )

    encoded_new_types = encode_tlv(NEW_MESHCOP_DATASET)
    assert encoded_new_types == NEW_MESHCOP_DATASET_HEX


def test_parse_tlv() -> None:
    """Test the TLV parser."""
    dataset_tlv = (
        "0E080000000000010000000300000F35060004001FFFE0020811111111222222220708FDAD70BF"
        "E5AA15DD051000112233445566778899AABBCCDDEEFF030E4F70656E54687265616444656D6F01"
        "0212340410445F2B5CA6F2A93A55CE570A70EFEECB0C0402A0F7F8"
    )
    dataset = parse_tlv(dataset_tlv)
    assert dataset == {
        MeshcopTLVType.CHANNEL: Channel(
            MeshcopTLVType.CHANNEL, bytes.fromhex("00000f")
        ),
        MeshcopTLVType.PANID: MeshcopTLVItem(
            MeshcopTLVType.PANID, bytes.fromhex("1234")
        ),
        MeshcopTLVType.EXTPANID: MeshcopTLVItem(
            MeshcopTLVType.EXTPANID, bytes.fromhex("1111111122222222")
        ),
        MeshcopTLVType.NETWORKNAME: NetworkName(
            MeshcopTLVType.NETWORKNAME, "OpenThreadDemo".encode()
        ),
        MeshcopTLVType.PSKC: MeshcopTLVItem(
            MeshcopTLVType.PSKC, bytes.fromhex("445f2b5ca6f2a93a55ce570a70efeecb")
        ),
        MeshcopTLVType.NETWORKKEY: MeshcopTLVItem(
            MeshcopTLVType.NETWORKKEY, bytes.fromhex("00112233445566778899aabbccddeeff")
        ),
        MeshcopTLVType.MESHLOCALPREFIX: MeshcopTLVItem(
            MeshcopTLVType.MESHLOCALPREFIX, bytes.fromhex("fdad70bfe5aa15dd")
        ),
        MeshcopTLVType.SECURITYPOLICY: MeshcopTLVItem(
            MeshcopTLVType.SECURITYPOLICY, bytes.fromhex("02a0f7f8")
        ),
        MeshcopTLVType.ACTIVETIMESTAMP: Timestamp(
            MeshcopTLVType.ACTIVETIMESTAMP, bytes.fromhex("0000000000010000")
        ),
        MeshcopTLVType.CHANNELMASK: MeshcopTLVItem(
            MeshcopTLVType.CHANNELMASK, bytes.fromhex("0004001fffe0")
        ),
    }

    parsed_new_types = parse_tlv(NEW_MESHCOP_DATASET_HEX)
    assert parsed_new_types == NEW_MESHCOP_DATASET


def test_parse_tlv_with_wakeup_channel() -> None:
    """Test the TLV parser from a (truncated) dataset from an Apple BR."""
    dataset_tlv = (
        "0e08000065901a07000000030000194a0300000f35060004001fffc003104d79486f6d65313233"
        "31323331323334"
    )
    dataset = parse_tlv(dataset_tlv)
    assert dataset == {
        MeshcopTLVType.ACTIVETIMESTAMP: Timestamp(
            MeshcopTLVType.ACTIVETIMESTAMP, bytes.fromhex("000065901a070000")
        ),
        MeshcopTLVType.CHANNEL: Channel(
            MeshcopTLVType.CHANNEL, bytes.fromhex("000019")
        ),
        MeshcopTLVType.WAKEUP_CHANNEL: MeshcopTLVItem(
            MeshcopTLVType.WAKEUP_CHANNEL, bytes.fromhex("00000f")
        ),
        MeshcopTLVType.CHANNELMASK: MeshcopTLVItem(
            MeshcopTLVType.CHANNELMASK, bytes.fromhex("0004001fffc0")
        ),
        MeshcopTLVType.NETWORKNAME: NetworkName(
            MeshcopTLVType.NETWORKNAME, "MyHome1231231234".encode()
        ),
    }


@pytest.mark.parametrize(
    "tlv, error, msg",
    (
        (
            "killevippen",
            TLVError,
            "invalid tlvs",
        ),
        (
            "FF",
            TLVError,
            "unknown type 255",
        ),
        (
            "030E4F70656E54687265616444656D",
            TLVError,
            "expected 14 bytes for NETWORKNAME, got 13",
        ),
        (
            "030E4F70656E54687265616444656DFF",
            TLVError,
            "invalid network name '4f70656e54687265616444656dff'",
        ),
    ),
)
def test_parse_tlv_error(tlv, error, msg) -> None:
    """Test the TLV parser error handling."""
    with pytest.raises(error, match=msg):
        parse_tlv(tlv)
