"""Test the Thread TLV parser."""

import pytest

from python_otbr_api.tlv_parser import MeshcopTLVType, TLVError, parse_tlv


def test_parse_tlv() -> None:
    """Test the TLV parser."""
    dataset_tlv = (
        "0E080000000000010000000300000F35060004001FFFE0020811111111222222220708FDAD70BF"
        "E5AA15DD051000112233445566778899AABBCCDDEEFF030E4F70656E54687265616444656D6F01"
        "0212340410445F2B5CA6F2A93A55CE570A70EFEECB0C0402A0F7F8"
    )
    dataset = parse_tlv(dataset_tlv)
    assert dataset == {
        MeshcopTLVType.CHANNEL: "00000f",
        MeshcopTLVType.PANID: "1234",
        MeshcopTLVType.EXTPANID: "1111111122222222",
        MeshcopTLVType.NETWORKNAME: "OpenThreadDemo",
        MeshcopTLVType.PSKC: "445f2b5ca6f2a93a55ce570a70efeecb",
        MeshcopTLVType.NETWORKKEY: "00112233445566778899aabbccddeeff",
        MeshcopTLVType.MESHLOCALPREFIX: "fdad70bfe5aa15dd",
        MeshcopTLVType.SECURITYPOLICY: "02a0f7f8",
        MeshcopTLVType.ACTIVETIMESTAMP: "0000000000010000",
        MeshcopTLVType.CHANNELMASK: "0004001fffe0",
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
