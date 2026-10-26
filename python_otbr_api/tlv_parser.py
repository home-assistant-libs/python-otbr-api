"""Parse datasets TLV encoded as specified by Thread."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import struct
import logging

_LOGGER = logging.getLogger(__name__)


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
    DURATION = 23
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
    THREAD_DOMAIN_NAME = 59
    WAKEUP_CHANNEL = 74
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

    @classmethod
    def from_channel(cls, channel: int) -> Channel:
        """Construct a channel on channel page 0.

        Raises TLVError if the channel doesn't fit the wire format.
        """
        if not 0 < channel < 2**16:
            raise TLVError(f"invalid channel '{channel}'")
        return cls(MeshcopTLVType.CHANNEL, struct.pack("!BH", 0, channel))


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
        try:
            unpacked: int = struct.unpack("!Q", self.data)[0]
        except struct.error as err:
            raise TLVError(f"invalid timestamp '{self.data.hex()}'") from err
        self.authoritative = bool(unpacked & 1)
        self.seconds = unpacked >> 16
        self.ticks = (unpacked >> 1) & 0x7FFF

    @classmethod
    def from_values(
        cls,
        tag: MeshcopTLVType,
        seconds: int,
        ticks: int = 0,
        authoritative: bool = False,
    ) -> Timestamp:
        """Construct a timestamp from its field values.

        Raises TLVError if seconds or ticks don't fit the wire format.
        """
        if not 0 <= seconds < 2**48:
            raise TLVError(f"timestamp seconds out of range: {seconds}")
        if not 0 <= ticks < 2**15:
            raise TLVError(f"timestamp ticks out of range: {ticks}")
        packed = (seconds << 16) | (ticks << 1) | int(authoritative)
        return cls(tag, struct.pack("!Q", packed))


@dataclass
class DelayTimer(MeshcopTLVItem):
    """Delay timer."""

    delay: int = field(init=False)

    def __post_init__(self) -> None:
        """Decode the delay in milliseconds.

        Raises TLVError if the data is not the four bytes the wire format
        defines, so a malformed delay timer is rejected instead of being
        accepted at whatever width it arrived with.
        """
        try:
            self.delay = struct.unpack("!L", self.data)[0]
        except struct.error as err:
            raise TLVError(f"invalid delay timer '{self.data.hex()}'") from err

    @classmethod
    def from_milliseconds(cls, delay: int) -> DelayTimer:
        """Construct a delay timer from a delay in milliseconds.

        Raises TLVError if the delay doesn't fit the wire format.
        """
        if not 0 <= delay < 2**32:
            raise TLVError(f"delay timer out of range: {delay}")
        return cls(MeshcopTLVType.DELAYTIMER, struct.pack("!L", delay))


def pending_channel_change(
    active: dict[MeshcopTLVType | int, MeshcopTLVItem], channel: int, delay: int
) -> dict[MeshcopTLVType | int, MeshcopTLVItem]:
    """Return the pending dataset moving an active dataset to a channel.

    The active timestamp goes up one second, or starts at one, and the pending
    timestamp matches it; the delay is in milliseconds. Raises TLVError for a
    channel outside 11 to 26 or a timestamp that cannot go up.
    """
    if not 11 <= channel <= 26:
        raise TLVError(f"invalid channel '{channel}'")
    stamp = active.get(MeshcopTLVType.ACTIVETIMESTAMP)
    seconds, ticks, authoritative = (
        (stamp.seconds + 1, stamp.ticks, stamp.authoritative)
        if isinstance(stamp, Timestamp)
        else (1, 0, False)
    )
    pending = dict(active)
    pending[MeshcopTLVType.CHANNEL] = Channel.from_channel(channel)
    pending[MeshcopTLVType.ACTIVETIMESTAMP] = Timestamp.from_values(
        MeshcopTLVType.ACTIVETIMESTAMP, seconds, ticks, authoritative
    )
    pending[MeshcopTLVType.PENDINGTIMESTAMP] = Timestamp.from_values(
        MeshcopTLVType.PENDINGTIMESTAMP, seconds, ticks
    )
    pending[MeshcopTLVType.DELAYTIMER] = DelayTimer.from_milliseconds(delay)
    return pending


def _encode_item(item: MeshcopTLVItem) -> bytes:
    """Encode a dataset item to TLV format."""
    data_len = len(item.data)
    return struct.pack(f"!BB{data_len}s", item.tag, data_len, item.data)


def encode_tlv(items: dict[MeshcopTLVType | int, MeshcopTLVItem]) -> str:
    """Encode a TLV encoded dataset to a hex string.

    Raises if the TLV is invalid.
    """
    result = b""

    for item in items.values():
        result += _encode_item(item)

    return result.hex()


def _parse_item(tag: MeshcopTLVType | int, data: bytes) -> MeshcopTLVItem:
    """Parse a TLV encoded dataset item."""
    if tag in (MeshcopTLVType.ACTIVETIMESTAMP, MeshcopTLVType.PENDINGTIMESTAMP):
        return Timestamp(tag, data)
    if tag == MeshcopTLVType.CHANNEL:
        return Channel(tag, data)
    if tag == MeshcopTLVType.DELAYTIMER:
        return DelayTimer(tag, data)
    if tag == MeshcopTLVType.NETWORKNAME:
        return NetworkName(tag, data)

    return MeshcopTLVItem(tag, data)


def parse_tlv(data: str) -> dict[MeshcopTLVType | int, MeshcopTLVItem]:
    """Parse a TLV encoded dataset.

    Raises if the TLV is invalid.
    """
    try:
        data_bytes = bytes.fromhex(data)
    except ValueError as err:
        raise TLVError("invalid tlvs") from err
    result = {}
    pos = 0
    length = len(data_bytes)

    while pos < length:
        if pos + 2 > length:
            raise TLVError("truncated tlv header")

        raw_tag = data_bytes[pos]
        pos += 1

        # Unknown tags should still be passed through
        tag: MeshcopTLVType | int

        try:
            tag = MeshcopTLVType(raw_tag)
        except ValueError:
            tag = raw_tag

        _len = data_bytes[pos]
        pos += 1

        if pos + _len > length:
            raise TLVError(f"expected {_len} bytes for tag {tag!r}, got {length - pos}")

        val = data_bytes[pos : pos + _len]
        pos += _len

        # Log unknown TLVs by type and length only: the value may hold
        # network credentials, which don't belong in the log.
        if not isinstance(tag, MeshcopTLVType):
            _LOGGER.warning("unknown TLV type %d (%d bytes)", raw_tag, _len)

        if tag in result:
            raise TLVError(f"duplicated tag {tag!r}")
        result[tag] = _parse_item(tag, val)
    return result
