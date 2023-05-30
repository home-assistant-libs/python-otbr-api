"""Calculate Thread PSKc.

Based on https://github.com/openthread/ot-br-posix/blob/main/src/utils/pskc.cpp
"""

import struct

from cryptography.hazmat.primitives import cmac
from cryptography.hazmat.primitives.ciphers import algorithms

AES_128_KEY_LEN = 16
ITERATION_COUNTS = 16384
BLKSIZE = 16
SALT_PREFIX = "Thread".encode()


def _derive_key(passphrase: str) -> bytes:
    """Derive key from passphrase according to RFC 4615."""
    passphrase_bytes = passphrase.encode()
    if len(passphrase_bytes) == AES_128_KEY_LEN:
        return passphrase_bytes
    c = cmac.CMAC(algorithms.AES128(b"\0" * AES_128_KEY_LEN))
    c.update(passphrase_bytes)
    return c.finalize()


def compute_pskc(ext_pan_id: bytes, network_name: str, passphrase: str) -> bytes:
    """Compute Thread PSKc."""
    salt = SALT_PREFIX + ext_pan_id + network_name.encode()
    key = _derive_key(passphrase)

    block_counter = 1
    prf_input = salt + struct.pack("!L", block_counter)

    # Calculate U_1
    c = cmac.CMAC(algorithms.AES128(key))
    c.update(prf_input)
    prf_output = c.finalize()
    pskc = bytearray(prf_output)

    for _ in range(ITERATION_COUNTS - 1):
        prf_input = prf_output

        # Calculate U_i
        c = cmac.CMAC(algorithms.AES128(key))
        c.update(prf_input)
        prf_output = c.finalize()

        # xor
        for i in range(BLKSIZE):
            pskc[i] ^= prf_output[i]

    return pskc
