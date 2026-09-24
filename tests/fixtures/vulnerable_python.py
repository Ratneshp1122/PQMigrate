# Fixture: known-vulnerable Python cryptography usage
# This file is intentionally insecure — for test purposes ONLY

from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519
from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1
from cryptography.hazmat.primitives.ciphers import Cipher
import hashlib
import ssl

# RSA key generation — CRITICAL
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# ECDSA with P-256 — CRITICAL
ec_key = ec.generate_private_key(SECP256R1())

# Ed25519 — CRITICAL
ed_key = ed25519.Ed25519PrivateKey.generate()

# MD5 — MEDIUM
def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()

# SHA-1 — MEDIUM
def legacy_hash(data):
    return hashlib.sha1(data).hexdigest()

# SHA-256 — SAFE
def good_hash(data):
    return hashlib.sha256(data).hexdigest()

# SSL context — HIGH
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
