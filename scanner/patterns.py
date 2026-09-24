"""
Crypto Primitive Pattern Registry
====================================
Single source of truth for every crypto primitive the scanner detects.
Each pattern records:
  - What the primitive is
  - Whether it's broken by Shor's / Grover's algorithm
  - Risk classification (CRITICAL / HIGH / MEDIUM / SAFE)
  - Whether "harvest now, decrypt later" applies
  - What to migrate to
  - NIST/CISA guidance
"""

from dataclasses import dataclass
from enum import Enum


class Risk(str, Enum):
    CRITICAL = "CRITICAL"  # Directly broken by Shor (RSA, DH, DSA, ECDH, ECDSA)
    HIGH     = "HIGH"      # Weakened significantly (AES-128, SHA-256 via Grover; deprecated TLS)
    MEDIUM   = "MEDIUM"    # Classically weak or deprecated (MD5, SHA-1, 3DES)
    SAFE     = "SAFE"      # Already PQC / quantum-resistant


class Family(str, Enum):
    KEM      = "key_exchange"     # Key exchange / encapsulation (classical)
    SIG      = "signature"        # Digital signatures (classical)
    HASH     = "hash"             # Hash functions
    SYM      = "symmetric"        # Symmetric encryption
    TLS      = "tls"              # TLS/SSL configuration
    PQC_KEM  = "pqc_kem"         # Already-PQC key encapsulation ✓
    PQC_SIG  = "pqc_sig"         # Already-PQC signature ✓
    HYBRID   = "hybrid"           # Classical+PQC hybrid ✓


@dataclass(frozen=True)
class Pattern:
    name:         str
    family:       Family
    risk:         Risk
    harvest_risk: bool    # True = data protected today readable by future QC
    replacement:  str     # What to migrate to
    guidance:     str     # One-line action


# ── Risk sort order for report output ─────────────────────────────────────────
RISK_ORDER = {Risk.CRITICAL: 0, Risk.HIGH: 1, Risk.MEDIUM: 2, Risk.SAFE: 3}


# ══════════════════════════════════════════════════════════════════════════════
# IMPORT PATTERNS
# Keyed by the full dotted module path that appears in import statements.
# ══════════════════════════════════════════════════════════════════════════════
IMPORT_PATTERNS: dict[str, Pattern] = {

    # ── RSA ───────────────────────────────────────────────────────────────────
    "cryptography.hazmat.primitives.asymmetric.rsa": Pattern(
        name="RSA",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="ML-KEM-768 (FIPS 203) for encapsulation; ML-DSA-65 (FIPS 204) for signatures",
        guidance="RSA is broken by Shor's algorithm. Migrate to NIST PQC immediately.",
    ),
    "cryptography.hazmat.primitives.asymmetric.padding": Pattern(
        name="RSA padding (OAEP / PKCS1v15)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="ML-KEM-768",
        guidance="RSA padding implies RSA key exchange — broken by Shor. Migrate to ML-KEM-768.",
    ),
    "Crypto.PublicKey.RSA": Pattern(
        name="RSA (pycryptodome)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="ML-KEM-768 + ML-DSA-65",
        guidance="RSA is broken by Shor's algorithm. Replace with NIST-standardized PQC.",
    ),
    "Crypto.Cipher.PKCS1_OAEP": Pattern(
        name="RSA-OAEP encryption (pycryptodome)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="ML-KEM-768",
        guidance="RSA-OAEP broken by Shor. Migrate key encapsulation to ML-KEM-768.",
    ),
    "Crypto.Signature.pkcs1_15": Pattern(
        name="RSA PKCS#1 v1.5 signatures",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65",
        guidance="RSA signatures broken by Shor. Migrate to ML-DSA-65 (FIPS 204).",
    ),
    "Crypto.Signature.pss": Pattern(
        name="RSA-PSS signatures",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65",
        guidance="RSA-PSS broken by Shor. Migrate to ML-DSA-65.",
    ),

    # ── DSA ───────────────────────────────────────────────────────────────────
    "cryptography.hazmat.primitives.asymmetric.dsa": Pattern(
        name="DSA",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65 (FIPS 204)",
        guidance="DSA (discrete log) broken by Shor. Migrate to ML-DSA-65.",
    ),
    "Crypto.PublicKey.DSA": Pattern(
        name="DSA (pycryptodome)",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65",
        guidance="DSA broken by Shor. Migrate to ML-DSA-65.",
    ),
    "Crypto.Signature.DSS": Pattern(
        name="ECDSA/DSS (pycryptodome)",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65",
        guidance="ECDSA broken by Shor. Migrate to ML-DSA-65.",
    ),

    # ── Diffie-Hellman ────────────────────────────────────────────────────────
    "cryptography.hazmat.primitives.asymmetric.dh": Pattern(
        name="DH (Diffie-Hellman)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="Hybrid X25519+ML-KEM-768 or ML-KEM-768 alone",
        guidance="DH key exchange broken by Shor. Migrate to ML-KEM-768 (FIPS 203).",
    ),

    # ── Elliptic Curve ────────────────────────────────────────────────────────
    "cryptography.hazmat.primitives.asymmetric.ec": Pattern(
        name="Elliptic Curve (ECDH / ECDSA)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="Hybrid X25519+ML-KEM-768 (key exchange) or ML-DSA-65 (signatures)",
        guidance="ECDLP broken by Shor. Use Hybrid X25519+ML-KEM-768 during transition period.",
    ),
    "cryptography.hazmat.primitives.asymmetric.x25519": Pattern(
        name="X25519 (ECDH)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="Hybrid X25519+ML-KEM-768",
        guidance="X25519 ECDH broken by Shor. Add ML-KEM-768 — same pattern as Chrome/Signal.",
    ),
    "cryptography.hazmat.primitives.asymmetric.x448": Pattern(
        name="X448 (ECDH)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="Hybrid X448+ML-KEM-1024",
        guidance="X448 ECDH broken by Shor. Pair with ML-KEM-1024 for hybrid.",
    ),
    "cryptography.hazmat.primitives.asymmetric.ed25519": Pattern(
        name="Ed25519 (signatures)",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65 (FIPS 204)",
        guidance="Ed25519 ECDLP broken by Shor. Migrate to ML-DSA-65.",
    ),
    "cryptography.hazmat.primitives.asymmetric.ed448": Pattern(
        name="Ed448 (signatures)",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-87 (FIPS 204)",
        guidance="Ed448 ECDLP broken by Shor. Migrate to ML-DSA-87.",
    ),
    "Crypto.PublicKey.ECC": Pattern(
        name="ECC (pycryptodome)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="Hybrid X25519+ML-KEM-768 or ML-DSA-65",
        guidance="ECC broken by Shor. Migrate to NIST PQC standards.",
    ),

    # ── Weak symmetric ────────────────────────────────────────────────────────
    "cryptography.hazmat.primitives.ciphers.algorithms.TripleDES": Pattern(
        name="3DES / Triple-DES",
        family=Family.SYM,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="AES-256-GCM",
        guidance="3DES deprecated by NIST SP 800-131A. Migrate to AES-256-GCM.",
    ),
    "cryptography.hazmat.primitives.ciphers.algorithms.Blowfish": Pattern(
        name="Blowfish",
        family=Family.SYM,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="AES-256-GCM",
        guidance="Blowfish is deprecated. Use AES-256-GCM.",
    ),
    "cryptography.hazmat.primitives.ciphers.algorithms.ARC4": Pattern(
        name="RC4",
        family=Family.SYM,
        risk=Risk.HIGH,
        harvest_risk=False,
        replacement="AES-256-GCM",
        guidance="RC4 is broken (RFC 7465). Replace with AES-256-GCM.",
    ),
    "Crypto.Cipher.DES": Pattern(
        name="DES",
        family=Family.SYM,
        risk=Risk.HIGH,
        harvest_risk=False,
        replacement="AES-256-GCM",
        guidance="DES broken (56-bit key). Migrate to AES-256-GCM.",
    ),
    "Crypto.Cipher.DES3": Pattern(
        name="3DES (pycryptodome)",
        family=Family.SYM,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="AES-256-GCM",
        guidance="3DES deprecated. Migrate to AES-256-GCM.",
    ),
    "Crypto.Cipher.ARC2": Pattern(
        name="RC2",
        family=Family.SYM,
        risk=Risk.HIGH,
        harvest_risk=False,
        replacement="AES-256-GCM",
        guidance="RC2 is deprecated and weak. Use AES-256-GCM.",
    ),
    "Crypto.Cipher.ARC4": Pattern(
        name="RC4 (pycryptodome)",
        family=Family.SYM,
        risk=Risk.HIGH,
        harvest_risk=False,
        replacement="AES-256-GCM",
        guidance="RC4 is broken (RFC 7465). Use AES-256-GCM.",
    ),

    # ── SSL/TLS ───────────────────────────────────────────────────────────────
    "ssl": Pattern(
        name="ssl module (audit for deprecated protocols)",
        family=Family.TLS,
        risk=Risk.HIGH,
        harvest_risk=True,
        replacement="TLS 1.3 with hybrid key exchange",
        guidance="Audit ssl.PROTOCOL_* constants. Minimum TLS 1.3. Migrate to PQC key exchange.",
    ),
    "OpenSSL.crypto": Pattern(
        name="pyOpenSSL",
        family=Family.KEM,
        risk=Risk.HIGH,
        harvest_risk=True,
        replacement="cryptography library + pqcrypto / oqs for PQC",
        guidance="Audit OpenSSL.crypto usage. Migrate key exchange and signatures to PQC.",
    ),
    "OpenSSL.SSL": Pattern(
        name="pyOpenSSL SSL context",
        family=Family.TLS,
        risk=Risk.HIGH,
        harvest_risk=True,
        replacement="TLS 1.3 + hybrid key exchange",
        guidance="Audit OpenSSL.SSL context — ensure TLS 1.3 minimum, PQC key exchange.",
    ),

    # ── PQC — already safe ✓ ─────────────────────────────────────────────────
    "pqcrypto.kem.ml_kem_512": Pattern(
        name="ML-KEM-512 (FIPS 203, Category 1) ✓",
        family=Family.PQC_KEM,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already PQC — consider ML-KEM-768 for Category 3",
        guidance="ML-KEM-512 is NIST-standardized. Upgrade to ML-KEM-768 for higher assurance.",
    ),
    "pqcrypto.kem.ml_kem_768": Pattern(
        name="ML-KEM-768 (FIPS 203, Category 3) ✓",
        family=Family.PQC_KEM,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already PQC — recommended baseline",
        guidance="ML-KEM-768 is the NIST-recommended baseline for most applications.",
    ),
    "pqcrypto.kem.ml_kem_1024": Pattern(
        name="ML-KEM-1024 (FIPS 203, Category 5) ✓",
        family=Family.PQC_KEM,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already PQC — maximum security",
        guidance="ML-KEM-1024 provides maximum quantum security (Category 5).",
    ),
    "pqcrypto.sign.ml_dsa_44": Pattern(
        name="ML-DSA-44 (FIPS 204, Category 2) ✓",
        family=Family.PQC_SIG,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already PQC — consider ML-DSA-65 for Category 3",
        guidance="ML-DSA-44 is NIST-standardized. Consider ML-DSA-65 for Category 3.",
    ),
    "pqcrypto.sign.ml_dsa_65": Pattern(
        name="ML-DSA-65 (FIPS 204, Category 3) ✓",
        family=Family.PQC_SIG,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already PQC — recommended baseline",
        guidance="ML-DSA-65 is the NIST-recommended signature scheme.",
    ),
    "pqcrypto.sign.ml_dsa_87": Pattern(
        name="ML-DSA-87 (FIPS 204, Category 5) ✓",
        family=Family.PQC_SIG,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already PQC — maximum security",
        guidance="ML-DSA-87 provides maximum signature security.",
    ),
    "oqs": Pattern(
        name="liboqs (Open Quantum Safe) ✓",
        family=Family.PQC_KEM,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already using PQC library — audit specific algorithm choices",
        guidance="liboqs is the OQS reference. Ensure you're using ML-KEM / ML-DSA, not deprecated schemes.",
    ),
}

# ══════════════════════════════════════════════════════════════════════════════
# CALL PATTERNS
# Function calls that indicate crypto usage beyond import detection.
# Keyed by "module.function" string.
# ══════════════════════════════════════════════════════════════════════════════
CALL_PATTERNS: dict[str, Pattern] = {
    "hashlib.md5": Pattern(
        name="MD5 (hashlib)",
        family=Family.HASH,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="SHA-256 or SHA3-256",
        guidance="MD5 is classically broken (collision attacks). Replace with SHA-256.",
    ),
    "hashlib.sha1": Pattern(
        name="SHA-1 (hashlib)",
        family=Family.HASH,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="SHA-256 or SHA3-256",
        guidance="SHA-1 is deprecated (SHAttered attack, 2017). Replace with SHA-256.",
    ),
    "hashlib.new": Pattern(
        name="hashlib.new (audit algorithm argument)",
        family=Family.HASH,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="SHA-256 or SHA3-256 if currently using MD5/SHA-1",
        guidance="Audit hashlib.new() — if algorithm is 'md5' or 'sha1', replace with SHA-256.",
    ),
    # ── SAFE hash functions ─────────────────────────────────────────────────────
    "hashlib.sha256": Pattern(
        name="SHA-256 (hashlib) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="No action required",
        guidance="SHA-256 is quantum-safe. Grover's algorithm provides at most quadratic speedup, leaving ~128-bit post-quantum security.",
    ),
    "hashlib.sha512": Pattern(
        name="SHA-512 (hashlib) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="No action required",
        guidance="SHA-512 provides 256-bit post-quantum security against Grover's algorithm.",
    ),
    "hashlib.sha3_256": Pattern(
        name="SHA3-256 (hashlib) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="No action required",
        guidance="SHA3-256 is quantum-safe and not structurally related to SHA-2.",
    ),
    "hashlib.sha3_512": Pattern(
        name="SHA3-512 (hashlib) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="No action required",
        guidance="SHA3-512 provides 256-bit post-quantum security.",
    ),
}

# ══════════════════════════════════════════════════════════════════════════════
# ATTRIBUTE PATTERNS
# Specific attribute accesses that indicate deprecated/broken TLS config.
# ══════════════════════════════════════════════════════════════════════════════
ATTRIBUTE_PATTERNS: dict[str, Pattern] = {
    "ssl.PROTOCOL_SSLv2": Pattern(
        name="SSL 2.0 (COMPLETELY BROKEN)",
        family=Family.TLS,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="TLS 1.3",
        guidance="SSL 2.0 is completely broken. Upgrade to TLS 1.3 immediately.",
    ),
    "ssl.PROTOCOL_SSLv3": Pattern(
        name="SSL 3.0 (POODLE attack)",
        family=Family.TLS,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="TLS 1.3",
        guidance="SSL 3.0 broken by POODLE (2014). Upgrade to TLS 1.3 immediately.",
    ),
    "ssl.PROTOCOL_TLSv1": Pattern(
        name="TLS 1.0 (deprecated, RFC 8996)",
        family=Family.TLS,
        risk=Risk.HIGH,
        harvest_risk=True,
        replacement="TLS 1.3 minimum",
        guidance="TLS 1.0 deprecated by RFC 8996. Minimum: TLS 1.3.",
    ),
    "ssl.PROTOCOL_TLSv1_1": Pattern(
        name="TLS 1.1 (deprecated, RFC 8996)",
        family=Family.TLS,
        risk=Risk.HIGH,
        harvest_risk=True,
        replacement="TLS 1.3 minimum",
        guidance="TLS 1.1 deprecated by RFC 8996. Minimum: TLS 1.3.",
    ),
}
