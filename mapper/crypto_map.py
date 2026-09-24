"""
Crypto Migration Mapping Table
================================
Maps each vulnerable crypto primitive to:
  - Its NIST-recommended PQC replacement
  - Code migration examples (before / after)
  - References (FIPS standard, IETF draft)
"""

from dataclasses import dataclass


@dataclass
class MigrationPath:
    from_primitive: str
    to_primitive:   str
    fips_standard:  str
    nist_category:  str
    before_code:    str     # Python snippet: vulnerable usage
    after_code:     str     # Python snippet: migrated usage
    notes:          str
    references:     list[str]


MIGRATION_MAP: dict[str, MigrationPath] = {

    # ── RSA key encapsulation → ML-KEM-768 ────────────────────────────────────
    "RSA": MigrationPath(
        from_primitive="RSA-2048 / RSA-4096",
        to_primitive="ML-KEM-768 (FIPS 203, Category 3)",
        fips_standard="FIPS 203",
        nist_category="Category 3 (~AES-192 equivalent)",
        before_code='''\
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# Vulnerable: RSA key exchange
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
ciphertext = public_key.encrypt(
    plaintext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)''',
        after_code='''\
from pqcrypto.kem import ml_kem_768

# Quantum-safe: ML-KEM-768 (FIPS 203)
public_key, secret_key = ml_kem_768.keygen()

# Sender: encapsulate shared secret
ciphertext, shared_secret = ml_kem_768.encaps(public_key)

# Receiver: decapsulate shared secret
shared_secret = ml_kem_768.decaps(secret_key, ciphertext)

# Use shared_secret with AES-256-GCM for encryption''',
        notes="RSA key encapsulation maps directly to ML-KEM. RSA signatures map to ML-DSA-65. Wire overhead: 2272B vs 256B for RSA-2048 public key, but the security argument is incomparably stronger.",
        references=[
            "NIST FIPS 203 (ML-KEM): https://csrc.nist.gov/pubs/fips/203/final",
            "NIST SP 800-227 (migration): https://csrc.nist.gov/pubs/sp/800/227/ipd",
        ],
    ),

    # ── X25519 (ECDH) → Hybrid X25519+ML-KEM-768 ─────────────────────────────
    "X25519": MigrationPath(
        from_primitive="X25519 (Elliptic Curve Diffie-Hellman)",
        to_primitive="Hybrid X25519+ML-KEM-768 (IETF draft-tls-hybrid-design)",
        fips_standard="FIPS 203 (ML-KEM component)",
        nist_category="Hybrid: Classical Cat.1 + PQC Cat.3",
        before_code='''\
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

# Vulnerable: X25519 ECDH only
alice_sk = X25519PrivateKey.generate()
alice_pk = alice_sk.public_key()

bob_sk = X25519PrivateKey.generate()
bob_pk = bob_sk.public_key()

# Both derive the same shared secret
shared_secret = alice_sk.exchange(bob_pk)
# ... but Shor's algorithm can recover this from the public keys alone''',
        after_code='''\
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from pqcrypto.kem import ml_kem_768

# Quantum-safe: Hybrid X25519 + ML-KEM-768
# (Same construction used in Chrome 116+ and Signal PQXDH)

# Alice (initiator) generates:
alice_x_sk = X25519PrivateKey.generate()
alice_x_pk = alice_x_sk.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw)

# Bob generates X25519 + ML-KEM-768 keypairs:
bob_x_sk   = X25519PrivateKey.generate()
bob_x_pk   = bob_x_sk.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw)
bob_kem_pk, bob_kem_sk = ml_kem_768.keygen()

# Alice: compute X25519 shared secret + encapsulate ML-KEM shared secret
x_ss  = alice_x_sk.exchange(X25519PublicKey.from_public_bytes(bob_x_pk))
kem_ct, kem_ss = ml_kem_768.encaps(bob_kem_pk)

# Bob: compute X25519 shared secret + decapsulate ML-KEM shared secret
x_ss_b  = bob_x_sk.exchange(X25519PublicKey.from_public_bytes(alice_x_pk))
kem_ss_b = ml_kem_768.decaps(bob_kem_sk, kem_ct)

# Both: combine via HKDF-SHA384 (KEM combiner — Giacon-Heuer-Poettering 2018)
transcript = alice_x_pk + bob_x_pk + bob_kem_pk + kem_ct
session_key = HKDF(
    algorithm=hashes.SHA384(),
    length=32,
    salt=None,
    info=b"hybrid-pqc-v1:" + transcript,
).derive(x_ss + kem_ss)
# Secure if EITHER X25519 OR ML-KEM-768 holds''',
        notes="Hybrid is the IETF-recommended approach during the transition period. It's what Chrome and Signal deployed. The wire overhead is +1,216 bytes over X25519-only. The time overhead is +0.18ms.",
        references=[
            "IETF draft-ietf-tls-hybrid-design: https://datatracker.ietf.org/doc/draft-ietf-tls-hybrid-design/",
            "Signal PQXDH: https://signal.org/docs/specifications/pqxdh/",
            "Chrome X25519Kyber768: https://blog.chromium.org/2023/08/chrome-ships-websocket-over-http3.html",
            "KEM Combiners (Giacon 2018): https://eprint.iacr.org/2018/024",
        ],
    ),

    # ── ECDSA → ML-DSA-65 ─────────────────────────────────────────────────────
    "ECDSA": MigrationPath(
        from_primitive="ECDSA (P-256 / P-384 / secp256k1)",
        to_primitive="ML-DSA-65 (FIPS 204, Category 3)",
        fips_standard="FIPS 204",
        nist_category="Category 3",
        before_code='''\
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

# Vulnerable: ECDSA P-256
sk = ec.generate_private_key(ec.SECP256R1())
pk = sk.public_key()
signature = sk.sign(message, ec.ECDSA(hashes.SHA256()))
pk.verify(signature, message, ec.ECDSA(hashes.SHA256()))''',
        after_code='''\
from pqcrypto.sign import ml_dsa_65   # pip install pqcrypto

# Quantum-safe: ML-DSA-65 (FIPS 204, Category 3)
pk, sk = ml_dsa_65.generate_keypair()
signature = ml_dsa_65.sign(message, sk)
ml_dsa_65.verify(message, signature, pk)
# Public key: 1952B | Signature: 3309B''',
        notes="ML-DSA-65 signatures are larger (~3.3KB vs ~64B for ECDSA). This is a known tradeoff. For high-bandwidth scenarios, FALCON-512 gives smaller sigs (666B) but is harder to implement safely.",
        references=[
            "NIST FIPS 204 (ML-DSA): https://csrc.nist.gov/pubs/fips/204/final",
        ],
    ),

    # ── Ed25519 → ML-DSA-65 ───────────────────────────────────────────────────
    "Ed25519": MigrationPath(
        from_primitive="Ed25519 (EdDSA)",
        to_primitive="ML-DSA-65 (FIPS 204, Category 3)",
        fips_standard="FIPS 204",
        nist_category="Category 3",
        before_code='''\
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sk = Ed25519PrivateKey.generate()
pk = sk.public_key()
signature = sk.sign(message)
pk.verify(signature, message)''',
        after_code='''\
from pqcrypto.sign import ml_dsa_65

pk, sk = ml_dsa_65.generate_keypair()
signature = ml_dsa_65.sign(message, sk)
ml_dsa_65.verify(message, signature, pk)''',
        notes="Identical migration as ECDSA. Ed25519 is broken by Shor for the same reason (ECDLP).",
        references=["NIST FIPS 204: https://csrc.nist.gov/pubs/fips/204/final"],
    ),

    # ── SHA-1 → SHA-256 ───────────────────────────────────────────────────────
    "SHA-1": MigrationPath(
        from_primitive="SHA-1",
        to_primitive="SHA-256 / SHA3-256",
        fips_standard="FIPS 180-4 / FIPS 202",
        nist_category="N/A (classical, but weak)",
        before_code="import hashlib\nh = hashlib.sha1(data).hexdigest()",
        after_code="import hashlib\nh = hashlib.sha256(data).hexdigest()  # or sha3_256",
        notes="SHA-1 is classically broken (SHAttered 2017 — chosen-prefix collision). SHA-256 is quantum-safe for most purposes (Grover reduces it to 128-bit effective security).",
        references=["SHAttered: https://shattered.io/"],
    ),

    # ── MD5 → SHA-256 ─────────────────────────────────────────────────────────
    "MD5": MigrationPath(
        from_primitive="MD5",
        to_primitive="SHA-256 / SHA3-256",
        fips_standard="FIPS 180-4",
        nist_category="N/A (broken classically)",
        before_code="import hashlib\nh = hashlib.md5(data).hexdigest()",
        after_code="import hashlib\nh = hashlib.sha256(data).hexdigest()",
        notes="MD5 is broken classically (collision attacks). Replace with SHA-256 unless you specifically need a non-cryptographic hash (in which case use xxhash or similar).",
        references=["RFC 6151: https://www.rfc-editor.org/rfc/rfc6151"],
    ),
}
