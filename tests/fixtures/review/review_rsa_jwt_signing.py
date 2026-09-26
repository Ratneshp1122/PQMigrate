"""Static-analysis fixture: RSA key used for a JWT signature.

This file is scan input only. The review does not execute it.
"""

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa


def issue_token(subject: str) -> str:
    signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return jwt.encode({"sub": subject}, signing_key, algorithm="RS256")
