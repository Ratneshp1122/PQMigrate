"""Static-analysis fixture: RSA encrypts a generated session key.

This file is scan input only. The review does not execute it.
"""

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def wrap_session_key() -> bytes:
    transport_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    session_key = os.urandom(32)
    return transport_key.public_key().encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
