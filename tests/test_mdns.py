"""Test decoding fields in _meshcop._udp.local. services."""

import pytest

from python_otbr_api.mdns import (
    Availability,
    ConnectionMode,
    StateBitmap,
    ThreadInterfaceStatus,
)


@pytest.mark.parametrize(
    "encoded, decoded",
    [
        (
            b"\x00\x00\x01\xb1",
            StateBitmap(
                connection_mode=ConnectionMode.PSKC,
                thread_interface_status=ThreadInterfaceStatus.ACTIVE,
                availability=Availability.HIGH,
                is_active=True,
                is_primary=True,
            ),
        ),
        (
            b"\x00\x00\x00!",
            StateBitmap(
                connection_mode=ConnectionMode.PSKC,
                thread_interface_status=ThreadInterfaceStatus.NOT_INITIALIZED,
                availability=Availability.HIGH,
                is_active=False,
                is_primary=False,
            ),
        ),
    ],
)
def test_decode_state_bitmap(encoded, decoded) -> None:
    """Test the TLV parser."""
    assert StateBitmap.from_bytes(encoded) == decoded


@pytest.mark.parametrize(
    "encoded, error",
    [
        # Input not bytes
        ("blah", TypeError),
        # Wrong length
        (b"\x00\x01\xb1", ValueError),
        # Padding not zeroed
        (b"\xff\x00\x01\xb1", ValueError),
        # Invalid ConnectionMode
        (b"\x00\x00\x01\xb5", ValueError),
        # Invalid ThreadInterfaceStatus
        (b"\x00\x00\x01\xb9", ValueError),
        # Invalid Availability
        (b"\x00\x00\x01\xf1", ValueError),
    ],
)
def test_decode_state_bitmap_error(encoded, error) -> None:
    """Test the TLV parser."""
    with pytest.raises(error):
        StateBitmap.from_bytes(encoded)
