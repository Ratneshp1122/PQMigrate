import hashlib
from target import compute_hash

def test_hash():
    # This test hardcodes the expectation of an MD5 hash.
    # When the patcher upgrades target.py to SHA256, this test WILL FAIL!
    assert compute_hash(b'hello') == hashlib.md5(b'hello').digest()
