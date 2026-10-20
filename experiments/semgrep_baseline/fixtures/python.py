import hashlib as hs
from cryptography.hazmat.primitives.asymmetric import rsa as asymmetric
from hmac import new as make_mac

# These are engineering matcher tests, not study gold or training cases.
# ruleid: pqmigrate.python.key-generation
private = asymmetric.generate_private_key(public_exponent=65537, key_size=2048)
# ruleid: pqmigrate.python.hashlib
hashed = hs.sha256(b'engineering fixture')
# ruleid: pqmigrate.python.hmac
mac = make_mac(b'key', b'message', 'sha256')
# ruleid: pqmigrate.python.candidate-sign
signature = private.sign(b'data', padding, algorithm)
# ruleid: pqmigrate.python.candidate-sign
document.sign('approval')  # Receiver stays uncertain; not proof of crypto.
# ok: pqmigrate.python.candidate-sign
sign = 'a string containing sign(data)'
# ok: pqmigrate.python.candidate-sign
def sign(data):
    return data
# ok: pqmigrate.python.key-generation
from cryptography.hazmat.primitives.asymmetric import rsa
