"""Utility function to decode fields in _meshcop._udp.local. mDNS services.

The implementation is based on the Open Thread implementation:
https://github.com/openthread/ot-br-posix/blob/8a8b2411abcf68659c25bb97672bdd2e5e724dcc/src/border_agent/border_agent.cpp#L109
"""

from dataclasses import dataclass
from enum import IntEnum

import bitstruct  # type: ignore[import]
from typing_extensions import Self


class ConnectionMode(IntEnum):
    """Connection mode."""

    DISABLED = 0
    PSKC = 1
    PSKD = 2
    VENDOR = 3
    X509 = 4


class ThreadInterfaceStatus(IntEnum):
    """Thread interface status."""

    NOT_INITIALIZED = 0
    INITIALIZED = 1
    ACTIVE = 2


class Availability(IntEnum):
    """Availability."""

    INFREQUENT = 0
    HIGH = 1


STATE_BITMAP_FORMAT = "u23u1u1u2u2u3"


@dataclass
class StateBitmap:
    """State bitmap."""

    connection_mode: ConnectionMode
    thread_interface_status: ThreadInterfaceStatus
    availability: Availability
    is_active: bool
    is_primary: bool

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """Decode from bytes."""
        if len(data) != 4:
            raise ValueError("Incorrect length")
        (
            padding,
            is_primary,
            is_active,
            availability,
            thread_if_status,
            connection_mode,
        ) = bitstruct.unpack(STATE_BITMAP_FORMAT, data)
        if padding != 0:
            raise ValueError(f"Could not decode '{data.hex}'")
        return cls(
            connection_mode=ConnectionMode(connection_mode),
            thread_interface_status=ThreadInterfaceStatus(thread_if_status),
            availability=Availability(availability),
            is_active=is_active,
            is_primary=is_primary,
        )
