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
