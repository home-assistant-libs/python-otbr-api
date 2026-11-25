"""Test the Thread TLV parser."""

import pytest

from python_otbr_api.tlv_parser import (
    Timestamp,
    Channel,
    DelayTimer,
    MeshcopTLVItem,
    MeshcopTLVType,
    NetworkName,
    TLVError,
    encode_tlv,
    parse_tlv,
    pending_channel_change,
)

# Shared dataset covering the newly added Meshcop TLV types.
NEW_MESHCOP_DATASET: dict[MeshcopTLVType | int, MeshcopTLVItem] = {
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
    MeshcopTLVType.PENDINGTIMESTAMP: Timestamp(
        MeshcopTLVType.PENDINGTIMESTAMP, bytes.fromhex("0000000000010000")
    ),
    MeshcopTLVType.DELAYTIMER: DelayTimer(
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
        189: MeshcopTLVItem(189, bytes.fromhex("abcdef")),
    }
    dataset_tlv = encode_tlv(dataset)
    assert (
        dataset_tlv
        == (
            "0E080000000000010000000300000F35060004001FFFE0020811111111222222220708FDAD"
            "70BFE5AA15DD051000112233445566778899AABBCCDDEEFF030E4F70656E54687265616444"
            "656D6F010212340410445F2B5CA6F2A93A55CE570A70EFEECB0C0402A0F7F8BD03ABCDEF"
        ).lower()
    )

    encoded_new_types = encode_tlv(NEW_MESHCOP_DATASET)
    assert encoded_new_types == NEW_MESHCOP_DATASET_HEX


def test_parse_tlv() -> None:
    """Test the TLV parser."""
    dataset_tlv = (
        "0E080000000000010000000300000F35060004001FFFE0020811111111222222220708FDAD70BF"
        "E5AA15DD051000112233445566778899AABBCCDDEEFF030E4F70656E54687265616444656D6F01"
        "0212340410445F2B5CA6F2A93A55CE570A70EFEECB0C0402A0F7F8BD03ABCDEF"
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
        189: MeshcopTLVItem(189, bytes.fromhex("abcdef")),
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
            "truncated tlv header",
        ),
        (
            "FF01",
            TLVError,
            "expected 1 bytes for tag 255, got 0",
        ),
        (
            "030E4F70656E54687265616444656D",
            TLVError,
            "expected 14 bytes for tag <MeshcopTLVType.NETWORKNAME: 3>, got 13",
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


def test_timestamp_parsing_full_integrity() -> None:
    """
    Test parsing of a timestamp with mixed values for seconds, ticks, and authoritative.

    We construct a value to ensure no bit overlap:
    - Seconds: 400 (0x190)
    - Ticks: 32767 (0x7FFF, Max value to catch the masking bug)
    - Authoritative: True (1)

    Hex Construction:
    - Seconds (48 bits): 00 00 00 00 01 90
    - Ticks/Auth (16 bits):
      (Ticks << 1) | Auth
      (0x7FFF << 1) | 1  =>  0xFFFE | 1  =>  0xFFFF

    Combined Hex: 000000000190FFFF
    """
    timestamp_data = bytes.fromhex("000000000190FFFF")
    timestamp = Timestamp(MeshcopTLVType.ACTIVETIMESTAMP, timestamp_data)

    # 1. Check Seconds: Ensures the upper 48 bits are shifted correctly
    assert timestamp.seconds == 400

    # 2. Check Ticks: Ensures the mask is 0x7FFF (32767)
    assert timestamp.ticks == 32767

    # 3. Check Authoritative: Ensures the lowest bit is read correctly
    assert timestamp.authoritative is True


def test_timestamp_from_values() -> None:
    """Test constructing a timestamp from field values."""
    timestamp = Timestamp.from_values(
        MeshcopTLVType.ACTIVETIMESTAMP, seconds=400, ticks=32767, authoritative=True
    )
    assert timestamp.data == bytes.fromhex("000000000190FFFF")
    assert timestamp.seconds == 400
    assert timestamp.ticks == 32767
    assert timestamp.authoritative is True

    pending = Timestamp.from_values(MeshcopTLVType.PENDINGTIMESTAMP, seconds=1)
    assert pending.tag == MeshcopTLVType.PENDINGTIMESTAMP
    assert pending.data == bytes.fromhex("0000000000010000")
    assert pending.ticks == 0
    assert pending.authoritative is False

    # The largest encodable timestamp survives a roundtrip
    ceiling = Timestamp.from_values(
        MeshcopTLVType.ACTIVETIMESTAMP, seconds=2**48 - 1, ticks=2**15 - 1
    )
    assert ceiling.seconds == 2**48 - 1
    assert ceiling.ticks == 2**15 - 1


@pytest.mark.parametrize(
    ("seconds", "ticks", "msg"),
    (
        (2**48, 0, "timestamp seconds out of range"),
        (-1, 0, "timestamp seconds out of range"),
        (0, 2**15, "timestamp ticks out of range"),
        (0, -1, "timestamp ticks out of range"),
    ),
)
def test_timestamp_from_values_out_of_range(seconds, ticks, msg) -> None:
    """Test constructing a timestamp from values which don't fit the wire format."""
    with pytest.raises(TLVError, match=msg):
        Timestamp.from_values(
            MeshcopTLVType.ACTIVETIMESTAMP, seconds=seconds, ticks=ticks
        )


def test_timestamp_invalid_data() -> None:
    """Test a malformed timestamp raises TLVError, not struct.error."""
    with pytest.raises(TLVError, match="invalid timestamp '00'"):
        Timestamp(MeshcopTLVType.ACTIVETIMESTAMP, bytes.fromhex("00"))
    # Also via the parser, as it would arrive from user supplied TLVs
    with pytest.raises(TLVError, match="invalid timestamp '00000000000100'"):
        parse_tlv("0E0700000000000100")


def test_pending_timestamp_and_delay_timer_parsed() -> None:
    """Test PENDINGTIMESTAMP and DELAYTIMER decode to typed items."""
    dataset = parse_tlv("33080000000000010000340400006699")
    pending = dataset[MeshcopTLVType.PENDINGTIMESTAMP]
    assert isinstance(pending, Timestamp)
    assert pending.seconds == 1
    delay = dataset[MeshcopTLVType.DELAYTIMER]
    assert isinstance(delay, DelayTimer)
    assert delay.delay == 0x6699


def test_delay_timer_from_milliseconds() -> None:
    """Test constructing a delay timer from a delay in milliseconds."""
    delay = DelayTimer.from_milliseconds(5 * 60 * 1000)
    assert delay.tag == MeshcopTLVType.DELAYTIMER
    assert delay.data == bytes.fromhex("000493E0")
    assert delay.delay == 300000
    assert encode_tlv({MeshcopTLVType.DELAYTIMER: delay}) == "3404000493e0"


@pytest.mark.parametrize("delay", (2**32, -1))
def test_delay_timer_out_of_range(delay) -> None:
    """Test constructing a delay timer which doesn't fit the wire format."""
    with pytest.raises(TLVError, match="delay timer out of range"):
        DelayTimer.from_milliseconds(delay)


def test_delay_timer_invalid_data() -> None:
    """Test a malformed delay timer raises TLVError, not struct.error."""
    with pytest.raises(TLVError, match="invalid delay timer '00'"):
        DelayTimer(MeshcopTLVType.DELAYTIMER, bytes.fromhex("00"))
    # Also via the parser, as it would arrive from user supplied TLVs
    with pytest.raises(TLVError, match="invalid delay timer '000000'"):
        parse_tlv("3403000000")


def test_unknown_tlv_value_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    """Test the unknown-TLV warning does not log the value."""
    parse_tlv("BD03ABCDEF")
    assert "unknown TLV type 189 (3 bytes)" in caplog.text
    assert "abcdef" not in caplog.text.lower()


ACTIVE_DATASET = parse_tlv(
    "0E080000000000010000000300000F35060004001FFFE0020811111111222222220708FDAD"
    "70BFE5AA15DD051000112233445566778899AABBCCDDEEFF030E4F70656E54687265616444"
    "656D6F010212340410445F2B5CA6F2A93A55CE570A70EFEECB0C0402A0F7F8"
)
CHANGED_TAGS = {
    MeshcopTLVType.CHANNEL,
    MeshcopTLVType.ACTIVETIMESTAMP,
    MeshcopTLVType.PENDINGTIMESTAMP,
    MeshcopTLVType.DELAYTIMER,
}


def test_channel_from_channel() -> None:
    """A channel is encoded on channel page 0."""
    channel = Channel.from_channel(26)
    assert channel.data == bytes.fromhex("00001a")
    assert channel.channel == 26


@pytest.mark.parametrize("channel", [0, 2**16])
def test_channel_from_channel_out_of_range(channel: int) -> None:
    """A channel that doesn't fit the wire format is refused."""
    with pytest.raises(TLVError):
        Channel.from_channel(channel)


def test_pending_channel_change() -> None:
    """The channel moves, both timestamps go one second up, the rest stays."""
    active = dict(ACTIVE_DATASET)
    active[MeshcopTLVType.ACTIVETIMESTAMP] = Timestamp.from_values(
        MeshcopTLVType.ACTIVETIMESTAMP, 7, ticks=5, authoritative=True
    )
    active[MeshcopTLVType.WAKEUP_CHANNEL] = MeshcopTLVItem(
        MeshcopTLVType.WAKEUP_CHANNEL, bytes.fromhex("00000f")
    )
    active[0x7F] = MeshcopTLVItem(0x7F, b"\x01")

    pending = pending_channel_change(active, 16, 1234)

    channel = pending[MeshcopTLVType.CHANNEL]
    assert isinstance(channel, Channel)
    assert channel.channel == 16
    stamp = pending[MeshcopTLVType.ACTIVETIMESTAMP]
    assert isinstance(stamp, Timestamp)
    assert (stamp.seconds, stamp.ticks, stamp.authoritative) == (8, 5, True)
    pending_stamp = pending[MeshcopTLVType.PENDINGTIMESTAMP]
    assert isinstance(pending_stamp, Timestamp)
    assert (pending_stamp.seconds, pending_stamp.ticks) == (8, 5)
    delay = pending[MeshcopTLVType.DELAYTIMER]
    assert isinstance(delay, DelayTimer)
    assert delay.delay == 1234
    assert {k: v for k, v in pending.items() if k not in CHANGED_TAGS} == {
        k: v for k, v in active.items() if k not in CHANGED_TAGS
    }
    assert parse_tlv(encode_tlv(pending)) == pending


def test_pending_channel_change_without_timestamp() -> None:
    """An active dataset without a timestamp is stamped from one second."""
    active = dict(ACTIVE_DATASET)
    del active[MeshcopTLVType.ACTIVETIMESTAMP]

    pending = pending_channel_change(active, 16, 1234)

    stamp = pending[MeshcopTLVType.ACTIVETIMESTAMP]
    assert isinstance(stamp, Timestamp)
    assert (stamp.seconds, stamp.ticks, stamp.authoritative) == (1, 0, False)


@pytest.mark.parametrize("channel", [10, 27])
def test_pending_channel_change_invalid_channel(channel: int) -> None:
    """A channel outside 11 to 26 is refused."""
    with pytest.raises(TLVError):
        pending_channel_change(ACTIVE_DATASET, channel, 1234)


def test_pending_channel_change_exhausted_timestamp() -> None:
    """An active timestamp that cannot go up is refused."""
    active = dict(ACTIVE_DATASET)
    active[MeshcopTLVType.ACTIVETIMESTAMP] = Timestamp.from_values(
        MeshcopTLVType.ACTIVETIMESTAMP, 2**48 - 1
    )
    with pytest.raises(TLVError):
        pending_channel_change(active, 16, 1234)
