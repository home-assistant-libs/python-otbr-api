"""Test calculating PSKc."""

import pytest

from python_otbr_api.pskc import compute_pskc


@pytest.mark.parametrize(
    "ext_pan_id, network_name, passphrase, expected_pskc",
    [
        # Example from https://openthread.io/guides/border-router/tools#pskc_generator
        (
            bytes.fromhex("1234AAAA1234BBBB"),
            "MyOTBRNetwork",
            "J01NME",
            "ee4fb64e9341e13846bbe7e1c52b6785",
        ),
        # OTBR Web UI default
        (
            bytes.fromhex("1111111122222222"),
            "OpenThreadDemo",
            "j01Nme",
            "445f2b5ca6f2a93a55ce570a70efeecb",
        ),
        # 128 bit key
        (
            bytes.fromhex("1234AAAA1234BBBB"),
            "MyOTBRNetwork",
            "0123456789ABCDEF",
            "f1927f0ec11da1ac7ef4ee05e81fe0ce",
        ),
    ],
)
def test_compute_pskc(ext_pan_id, network_name, passphrase, expected_pskc) -> None:
    """Test the TLV parser."""
    assert expected_pskc == compute_pskc(ext_pan_id, network_name, passphrase).hex()
