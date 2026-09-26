import hashlib
from cryptography.hazmat.primitives.ciphers import algorithms

# This one is a known auto-patchable hash
def compute_hash(data):
    # Classical legacy hash
    # [PQMigrate Auto-Patch] Upgraded MD5 (hashlib) -> SHA-256 / SHA-3 (Ref: FIPS 180-4 / FIPS 202)
    return hashlib.sha256(data).digest()

def encrypt_data():
    # Classical AES-128
    return algorithms.AES(b'16bytekey1234567')

def _unresolved_key():
    from cryptography.hazmat.primitives.asymmetric import rsa
    return rsa
