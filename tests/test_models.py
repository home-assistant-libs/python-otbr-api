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


def test_serialize_active_dataset_dual_keys():
    """Test that as_json() emits both PascalCase and camelCase keys.

    ot-br-posix's REST API parses incoming payloads case-sensitively but
    silently ignores unknown keys. Emitting both capitalizations keeps the
    library compatible with both older routers (PascalCase) and newer ones
    (camelCase, per the OpenAPI spec).
    """
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
    # Top-level keys must be present in BOTH capitalizations.
    for camel, pascal in (
        ("activeTimestamp", "ActiveTimestamp"),
        ("networkKey", "NetworkKey"),
        ("networkName", "NetworkName"),
        ("extPanId", "ExtPanId"),
        ("meshLocalPrefix", "MeshLocalPrefix"),
        ("panId", "PanId"),
        ("channel", "Channel"),
        ("pskc", "PSKc"),
        ("securityPolicy", "SecurityPolicy"),
        ("channelMask", "ChannelMask"),
    ):
        assert camel in result, f"missing camelCase key {camel}"
        assert pascal in result, f"missing PascalCase key {pascal}"
        assert result[camel] == result[pascal]
    # Nested dicts must also expose both capitalizations.
    for camel, pascal in (("seconds", "Seconds"), ("ticks", "Ticks")):
        assert camel in result["activeTimestamp"]
        assert pascal in result["activeTimestamp"]
    for camel, pascal in (
        ("rotationTime", "RotationTime"),
        ("obtainNetworkKey", "ObtainNetworkKey"),
        ("routers", "Routers"),
    ):
        assert camel in result["securityPolicy"]
        assert pascal in result["securityPolicy"]


def test_serialize_pending_dataset_dual_keys():
    """Test that PendingDataSet.as_json() emits both capitalizations."""
    pending = python_otbr_api.PendingDataSet(
        active_dataset=python_otbr_api.ActiveDataSet(network_name="OpenThread HA"),
        delay=30000,
        pending_timestamp=python_otbr_api.Timestamp(seconds=2, ticks=0),
    )
    result = pending.as_json()
    for camel, pascal in (
        ("activeDataset", "ActiveDataset"),
        ("delay", "Delay"),
        ("pendingTimestamp", "PendingTimestamp"),
    ):
        assert camel in result
        assert pascal in result
    assert "networkName" in result["activeDataset"]
    assert "NetworkName" in result["activeDataset"]


def test_roundtrip_dual_keys():
    """Test that from_json(as_json(x)) preserves data.

    from_json() must cope with dual-key input (both PascalCase and camelCase
    present at once), which is what as_json() now emits.
    """
    original = python_otbr_api.ActiveDataSet(
        network_name="Test", channel=15, pan_id=4660
    )
    roundtripped = python_otbr_api.ActiveDataSet.from_json(original.as_json())
    assert roundtripped == original
