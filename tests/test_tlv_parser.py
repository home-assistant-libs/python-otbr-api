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


def test_parse_tlv_apple() -> None:
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
        MeshcopTLVType.APPLE_TAG_UNKNOWN: MeshcopTLVItem(
            MeshcopTLVType.APPLE_TAG_UNKNOWN, bytes.fromhex("00000f")
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
