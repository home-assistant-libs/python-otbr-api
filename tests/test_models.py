"""Test data models."""

import python_otbr_api


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
                "Routers": True,
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
