"""Test data models."""

import python_otbr_api
from python_otbr_api.models import SecurityPolicy


def test_deserialize_pending_dataset():
    """Test deserializing a pending dataset."""
    assert python_otbr_api.PendingDataSet.from_json(
        {
            "ActiveDataset": {
                "NetworkName": "OpenThread HA",
            },
            "Delay": 12345,
            "PendingTimestamp": {},
        }
    ) == python_otbr_api.PendingDataSet(
        python_otbr_api.ActiveDataSet(network_name="OpenThread HA"),
        12345,
        python_otbr_api.Timestamp(),
    )


def test_deserialize_active_dataset_camelcase():
    """Test deserializing with camelCase keys as returned by the OTBR REST API."""
    dataset = python_otbr_api.ActiveDataSet.from_json(
        {
            "activeTimestamp": {"seconds": 1, "ticks": 0, "authoritative": False},
            "networkKey": "00112233445566778899aabbccddeeff",
            "networkName": "OpenThread-1234",
            "extPanId": "dead00beef00cafe",
            "meshLocalPrefix": "fd11:2222:3333::/64",
            "panId": 12345,
            "channel": 15,
            "pskc": "aabbccddeeff00112233445566778899",
            "securityPolicy": {
                "rotationTime": 672,
                "obtainNetworkKey": True,
                "routers": True,
            },
            "channelMask": 134215680,
        }
    )
    assert dataset.channel == 15
    assert dataset.network_name == "OpenThread-1234"
    assert dataset.extended_pan_id == "dead00beef00cafe"
    assert dataset.pan_id == 12345
    assert dataset.psk_c == "aabbccddeeff00112233445566778899"
    assert dataset.active_timestamp == python_otbr_api.Timestamp(
        authoritative=False, seconds=1, ticks=0
    )
    assert dataset.security_policy is not None
    assert dataset.security_policy.rotation_time == 672


def test_deserialize_pending_dataset_camelcase():
    """Test that camelCase works for PendingDataSet with nested objects."""
    result = python_otbr_api.PendingDataSet.from_json(
        {
            "activeDataset": {"networkName": "OpenThread HA"},
            "delay": 12345,
            "pendingTimestamp": {},
        }
    )
    assert result == python_otbr_api.PendingDataSet(
        python_otbr_api.ActiveDataSet(network_name="OpenThread HA"),
        12345,
        python_otbr_api.Timestamp(),
    )


def test_serialize_active_dataset_camelcase():
    """Test that as_json() emits camelCase keys matching the OTBR REST API."""
    dataset = python_otbr_api.ActiveDataSet(
        active_timestamp=python_otbr_api.Timestamp(
            authoritative=False, seconds=1, ticks=0
        ),
        network_key="00112233445566778899aabbccddeeff",
        network_name="OpenThread-1234",
        extended_pan_id="dead00beef00cafe",
        mesh_local_prefix="fd11:2222:3333::/64",
        pan_id=12345,
        channel=15,
        psk_c="aabbccddeeff00112233445566778899",
        security_policy=SecurityPolicy(
            rotation_time=672, obtain_network_key=True, routers=True
        ),
        channel_mask=134215680,
    )
    result = dataset.as_json()
    # All top-level keys must be camelCase
    assert "activeTimestamp" in result
    assert "networkKey" in result
    assert "networkName" in result
    assert "extPanId" in result
    assert "meshLocalPrefix" in result
    assert "panId" in result
    assert "channel" in result
    assert "pskc" in result
    assert "securityPolicy" in result
    assert "channelMask" in result
    # Nested keys must also be camelCase
    assert "seconds" in result["activeTimestamp"]
    assert "rotationTime" in result["securityPolicy"]
    assert "obtainNetworkKey" in result["securityPolicy"]


def test_serialize_pending_dataset_camelcase():
    """Test that PendingDataSet.as_json() emits camelCase keys."""
    pending = python_otbr_api.PendingDataSet(
        active_dataset=python_otbr_api.ActiveDataSet(network_name="OpenThread HA"),
        delay=30000,
        pending_timestamp=python_otbr_api.Timestamp(seconds=2, ticks=0),
    )
    result = pending.as_json()
    assert "activeDataset" in result
    assert "delay" in result
    assert "pendingTimestamp" in result
    assert "networkName" in result["activeDataset"]


def test_roundtrip_camelcase():
    """Test that from_json(as_json(x)) preserves data."""
    original = python_otbr_api.ActiveDataSet(
        network_name="Test", channel=15, pan_id=4660
    )
    roundtripped = python_otbr_api.ActiveDataSet.from_json(original.as_json())
    assert roundtripped == original
