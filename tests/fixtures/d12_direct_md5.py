import hashlib

label = "hashlib.md5(b'not code')"
# hashlib.md5(b"comment") must remain unchanged.
digest = hashlib.md5(b"review fixture").hexdigest()
