"""Parse datasets TLV encoded as specified by Thread."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import struct


class TLVError(Exception):
    """TLV error."""


class MeshcopTLVType(IntEnum):
    """Types."""

    CHANNEL = 0
    PANID = 1
    EXTPANID = 2
    NETWORKNAME = 3
    PSKC = 4
    NETWORKKEY = 5
    NETWORK_KEY_SEQUENCE = 6
    MESHLOCALPREFIX = 7
    STEERING_DATA = 8
    BORDER_AGENT_RLOC = 9
    COMMISSIONER_ID = 10
    COMM_SESSION_ID = 11
    SECURITYPOLICY = 12
    GET = 13
    ACTIVETIMESTAMP = 14
    COMMISSIONER_UDP_PORT = 15
    STATE = 16
    JOINER_DTLS = 17
    JOINER_UDP_PORT = 18
    JOINER_IID = 19
    JOINER_RLOC = 20
    JOINER_ROUTER_KEK = 21
    PROVISIONING_URL = 32
    VENDOR_NAME_TLV = 33
    VENDOR_MODEL_TLV = 34
    VENDOR_SW_VERSION_TLV = 35
    VENDOR_DATA_TLV = 36
    VENDOR_STACK_VERSION_TLV = 37
    UDP_ENCAPSULATION_TLV = 48
    IPV6_ADDRESS_TLV = 49
    PENDINGTIMESTAMP = 51
    DELAYTIMER = 52
    CHANNELMASK = 53
    COUNT = 54
    PERIOD = 55
    SCAN_DURATION = 56
    ENERGY_LIST = 57
    # Seen in a dataset imported through iOS companion app
    APPLE_TAG_UNKNOWN = 74
    DISCOVERYREQUEST = 128
    DISCOVERYRESPONSE = 129
    JOINERADVERTISEMENT = 241


@dataclass
class MeshcopTLVItem:
    """Base class for TLV items."""

    tag: int
    data: bytes

    def __str__(self) -> str:
        """Return a string representation."""
        return self.data.hex()


@dataclass
class Channel(MeshcopTLVItem):
    """Channel."""

    channel: int = field(init=False)

    def __post_init__(self) -> None:
        """Decode the channel."""
        self.channel = int.from_bytes(self.data, "big")
        if not self.channel:
            raise TLVError(f"invalid channel '{self.channel}'")


@dataclass
class NetworkName(MeshcopTLVItem):
    """Network name."""

    name: str = field(init=False)

    def __post_init__(self) -> None:
        """Decode the name."""
        try:
            self.name = self.data.decode()
        except UnicodeDecodeError as err:
            raise TLVError(f"invalid network name '{self.data.hex()}'") from err

    def __str__(self) -> str:
        return self.name


@dataclass
class Timestamp(MeshcopTLVItem):
    """Timestamp."""

    authoritative: bool = field(init=False)
    seconds: int = field(init=False)
    ticks: int = field(init=False)

    def __post_init__(self) -> None:
        """Decode the timestamp."""
        # The timestamps are packed in 8 bytes:
        # [seconds 48 bits][ticks 15 bits][authoritative flag 1 bit]
        unpacked: int = struct.unpack("!Q", self.data)[0]
        self.authoritative = bool(unpacked & 1)
        self.seconds = unpacked >> 16
        self.ticks = (unpacked >> 1) & 0x7FF


def _encode_item(item: MeshcopTLVItem) -> bytes:
    """Encode a dataset item to TLV format."""
    data_len = len(item.data)
    return struct.pack(f"!BB{data_len}s", item.tag, data_len, item.data)


def encode_tlv(items: dict[MeshcopTLVType, MeshcopTLVItem]) -> str:
    """Encode a TLV encoded dataset to a hex string.

    Raises if the TLV is invalid.
    """
    result = b""

    for item in items.values():
        result += _encode_item(item)

    return result.hex()


def _parse_item(tag: MeshcopTLVType, data: bytes) -> MeshcopTLVItem:
    """Parse a TLV encoded dataset item."""
    if tag == MeshcopTLVType.ACTIVETIMESTAMP:
        return Timestamp(tag, data)
    if tag == MeshcopTLVType.CHANNEL:
        return Channel(tag, data)
    if tag == MeshcopTLVType.NETWORKNAME:
        return NetworkName(tag, data)

    return MeshcopTLVItem(tag, data)


def parse_tlv(data: str) -> dict[MeshcopTLVType, MeshcopTLVItem]:
    """Parse a TLV encoded dataset.

    Raises if the TLV is invalid.
    """
    try:
        data_bytes = bytes.fromhex(data)
    except ValueError as err:
        raise TLVError("invalid tlvs") from err
    result = {}
    pos = 0
    while pos < len(data_bytes):
        try:
            tag = MeshcopTLVType(data_bytes[pos])
        except ValueError as err:
            raise TLVError(f"unknown type {data_bytes[pos]}") from err
        pos += 1
        _len = data_bytes[pos]
        pos += 1
        val = data_bytes[pos : pos + _len]
        if len(val) < _len:
            raise TLVError(f"expected {_len} bytes for {tag.name}, got {len(val)}")
        pos += _len
        if tag in result:
            raise TLVError(f"duplicated tag {tag.name}")
        result[tag] = _parse_item(tag, val)
    return result
