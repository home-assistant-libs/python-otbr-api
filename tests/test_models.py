"""Test data models."""

import python_otbr_api

ACTIVE_DATASET_CAMEL = {
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


def test_active_dataset_from_json():
    """Test parsing an ActiveDataSet from camelCase JSON."""
    dataset = python_otbr_api.ActiveDataSet.from_json(ACTIVE_DATASET_CAMEL)
    assert dataset.channel == 15
    assert dataset.network_name == "OpenThread-1234"
    assert dataset.active_timestamp == python_otbr_api.Timestamp(
        authoritative=False, seconds=1, ticks=0
    )
    assert dataset.security_policy.rotation_time == 672
    assert dataset.as_json() == ACTIVE_DATASET_CAMEL


PENDING_CAMEL = {
    "activeDataset": {"networkName": "OpenThread HA"},
    "delay": 12345,
    "pendingTimestamp": {},
}


def test_pending_dataset_from_json():
    """Test parsing a PendingDataSet, with nested objects."""
    result = python_otbr_api.PendingDataSet.from_json(PENDING_CAMEL)
    assert result == python_otbr_api.PendingDataSet(
        python_otbr_api.ActiveDataSet(network_name="OpenThread HA"),
        12345,
        python_otbr_api.Timestamp(),
    )
    assert result.as_json() == PENDING_CAMEL
