"""
Go Language Crypto Pattern Registry
=======================================
Covers Go standard library (crypto/*) and golang.org/x/crypto packages.

WHY GO MATTERS:
  Most modern infrastructure is written in Go — Kubernetes, Docker, Vault,
  Terraform, etcd, Consul, Prometheus. If any of these are in your stack
  they carry quantum-vulnerable crypto into your critical path.

HOW GO CRYPTO IS STRUCTURED:
  Go has two crypto package trees:
  1. stdlib: "crypto/rsa", "crypto/ecdsa", "crypto/tls" — in every Go install
  2. extended: "golang.org/x/crypto/..." — additional algorithms, SSH, bcrypt

  Go's import paths are always full, dotted strings in double quotes.
  Unlike Python there are no relative imports or aliased paths — every
  import is globally unique and fully qualified. This makes regex scanning
  99%+ accurate for Go.
"""

from .patterns import Pattern, Risk, Family


# ══════════════════════════════════════════════════════════════════════════════
# GO IMPORT PATTERNS
# Keyed by exact Go import path string.
# ══════════════════════════════════════════════════════════════════════════════
GO_IMPORT_PATTERNS: dict[str, Pattern] = {

    # ── CRITICAL: Broken by Shor's algorithm ──────────────────────────────────

    "crypto/rsa": Pattern(
        name="RSA (Go stdlib)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="ML-KEM-768 via github.com/open-quantum-safe/liboqs-go",
        guidance="crypto/rsa broken by Shor's algorithm. Migrate to ML-KEM-768 (FIPS 203).",
    ),
    "crypto/dsa": Pattern(
        name="DSA (Go stdlib)",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65 via liboqs-go",
        guidance="crypto/dsa broken by Shor's algorithm. Migrate to ML-DSA-65 (FIPS 204).",
    ),
    "crypto/ecdsa": Pattern(
        name="ECDSA (Go stdlib)",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65 via liboqs-go",
        guidance="crypto/ecdsa ECDLP broken by Shor. Migrate to ML-DSA-65 (FIPS 204).",
    ),
    "crypto/ecdh": Pattern(
        name="ECDH (Go stdlib)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="Hybrid X25519+ML-KEM-768 via liboqs-go",
        guidance="crypto/ecdh ECDLP broken by Shor. Add ML-KEM-768 for hybrid key exchange.",
    ),
    "crypto/elliptic": Pattern(
        name="Elliptic Curves (Go stdlib)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="Hybrid X25519+ML-KEM-768 via liboqs-go",
        guidance="crypto/elliptic P-256/P-384/P-521 broken by Shor. Migrate to ML-KEM/ML-DSA.",
    ),
    "golang.org/x/crypto/curve25519": Pattern(
        name="X25519 / Curve25519 (x/crypto)",
        family=Family.KEM,
        risk=Risk.CRITICAL,
        harvest_risk=True,
        replacement="Hybrid X25519+ML-KEM-768",
        guidance="X25519 ECDLP broken by Shor. Add ML-KEM-768 to create a hybrid (IETF pattern).",
    ),
    "golang.org/x/crypto/ed25519": Pattern(
        name="Ed25519 (x/crypto)",
        family=Family.SIG,
        risk=Risk.CRITICAL,
        harvest_risk=False,
        replacement="ML-DSA-65 via liboqs-go",
        guidance="Ed25519 ECDLP broken by Shor. Migrate to ML-DSA-65.",
    ),

    # ── HIGH: Deprecated protocols or requires deep audit ─────────────────────

    "crypto/tls": Pattern(
        name="TLS (Go stdlib — audit config)",
        family=Family.TLS,
        risk=Risk.HIGH,
        harvest_risk=True,
        replacement="TLS 1.3 minimum + Go 1.23 X25519MLKEM768 draft support",
        guidance="Audit tls.Config — set MinVersion=tls.VersionTLS13. "
                 "Go 1.23+ has experimental ML-KEM-768 key exchange.",
    ),
    "golang.org/x/crypto/ssh": Pattern(
        name="SSH (x/crypto/ssh)",
        family=Family.KEM,
        risk=Risk.HIGH,
        harvest_risk=True,
        replacement="SSH with PQC key exchange (draft-kampanakis-curdle-ssh-pq-kem)",
        guidance="SSH uses ECDH/RSA for key exchange — both broken by Shor. "
                 "Audit for PQC-capable key types when standard matures.",
    ),
    "golang.org/x/crypto/openpgp": Pattern(
        name="OpenPGP (x/crypto/openpgp)",
        family=Family.KEM,
        risk=Risk.HIGH,
        harvest_risk=True,
        replacement="OpenPGP with PQC (RFC draft-ounsworth-openpgp-pqc)",
        guidance="OpenPGP uses RSA/ECDH — both broken by Shor. Migrate to PQC key types.",
    ),
    "golang.org/x/crypto/rc4": Pattern(
        name="RC4 (x/crypto/rc4)",
        family=Family.SYM,
        risk=Risk.HIGH,
        harvest_risk=False,
        replacement="crypto/aes with GCM mode",
        guidance="RC4 broken by statistical bias (RFC 7465 — prohibited in TLS). Use AES-256-GCM.",
    ),

    # ── MEDIUM: Classically weak or deprecated ────────────────────────────────

    "crypto/md5": Pattern(
        name="MD5 (Go stdlib)",
        family=Family.HASH,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="crypto/sha256 or golang.org/x/crypto/sha3",
        guidance="MD5 broken by collision attacks. Replace with crypto/sha256.",
    ),
    "crypto/sha1": Pattern(
        name="SHA-1 (Go stdlib)",
        family=Family.HASH,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="crypto/sha256 or golang.org/x/crypto/sha3",
        guidance="SHA-1 deprecated (SHAttered 2017). Replace with crypto/sha256.",
    ),
    "golang.org/x/crypto/blowfish": Pattern(
        name="Blowfish (x/crypto)",
        family=Family.SYM,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="crypto/aes with GCM mode",
        guidance="Blowfish deprecated (64-bit block size). Use AES-256-GCM.",
    ),
    "golang.org/x/crypto/des": Pattern(
        name="DES / 3DES (x/crypto)",
        family=Family.SYM,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="crypto/aes with GCM mode",
        guidance="DES/3DES deprecated by NIST (SP 800-131A, 2023). Use AES-256-GCM.",
    ),
    "golang.org/x/crypto/cast5": Pattern(
        name="CAST5 (x/crypto)",
        family=Family.SYM,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="crypto/aes with GCM mode",
        guidance="CAST5 deprecated. Use AES-256-GCM.",
    ),
    "golang.org/x/crypto/twofish": Pattern(
        name="Twofish (x/crypto)",
        family=Family.SYM,
        risk=Risk.MEDIUM,
        harvest_risk=False,
        replacement="crypto/aes with GCM mode",
        guidance="Twofish not widely audited for production. Use AES-256-GCM.",
    ),

    # ── SAFE: Already quantum-resistant ✓ ─────────────────────────────────────

    "crypto/aes": Pattern(
        name="AES (Go stdlib) ✓",
        family=Family.SYM,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already safe — verify GCM mode, avoid ECB/CBC",
        guidance="AES is quantum-safe (Grover leaves 128-bit effective security for AES-256).",
    ),
    "crypto/sha256": Pattern(
        name="SHA-256 (Go stdlib) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already safe",
        guidance="SHA-256 is quantum-safe (128-bit effective via Grover).",
    ),
    "crypto/sha512": Pattern(
        name="SHA-512 (Go stdlib) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already safe",
        guidance="SHA-512 is quantum-safe.",
    ),
    "golang.org/x/crypto/chacha20poly1305": Pattern(
        name="ChaCha20-Poly1305 (x/crypto) ✓",
        family=Family.SYM,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already safe",
        guidance="ChaCha20-Poly1305 is quantum-safe and preferred for TLS 1.3.",
    ),
    "golang.org/x/crypto/chacha20": Pattern(
        name="ChaCha20 (x/crypto) ✓",
        family=Family.SYM,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already safe",
        guidance="ChaCha20 stream cipher is quantum-safe.",
    ),
    "golang.org/x/crypto/bcrypt": Pattern(
        name="bcrypt (x/crypto) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already safe for password hashing",
        guidance="bcrypt is safe for passwords. Consider Argon2 for new code.",
    ),
    "golang.org/x/crypto/argon2": Pattern(
        name="Argon2 (x/crypto) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already safe — recommended for new code",
        guidance="Argon2 is the recommended password hashing algorithm (PHC winner).",
    ),
    "golang.org/x/crypto/hkdf": Pattern(
        name="HKDF (x/crypto) ✓",
        family=Family.HASH,
        risk=Risk.SAFE,
        harvest_risk=False,
        replacement="Already safe — used in hybrid combiner",
        guidance="HKDF-SHA256/384 is safe and is the recommended KEM combiner.",
    ),
}

# ══════════════════════════════════════════════════════════════════════════════
# GO CALL/ATTRIBUTE PATTERNS
# Regex → (import_key, display_name)
# Catches function calls that don't always have explicit imports visible
# (e.g., in generated code, or when imported via dot-import)
# ══════════════════════════════════════════════════════════════════════════════
GO_CALL_PATTERNS: list[tuple[str, str, str]] = [
    # (regex pattern,                 pattern_key,      display label)
    (r'\brsa\.GenerateKey\s*\(',      "crypto/rsa",     "rsa.GenerateKey()"),
    (r'\brsa\.GenerateMultiPrimeKey\(', "crypto/rsa",   "rsa.GenerateMultiPrimeKey()"),
    (r'\brsa\.EncryptOAEP\s*\(',      "crypto/rsa",     "rsa.EncryptOAEP()"),
    (r'\brsa\.EncryptPKCS1v15\s*\(',  "crypto/rsa",     "rsa.EncryptPKCS1v15()"),
    (r'\brsa\.SignPKCS1v15\s*\(',      "crypto/rsa",     "rsa.SignPKCS1v15()"),
    (r'\brsa\.SignPSS\s*\(',           "crypto/rsa",     "rsa.SignPSS()"),
    (r'\becdsa\.GenerateKey\s*\(',    "crypto/ecdsa",   "ecdsa.GenerateKey()"),
    (r'\becdsa\.Sign\s*\(',           "crypto/ecdsa",   "ecdsa.Sign()"),
    (r'\becdsa\.SignASN1\s*\(',       "crypto/ecdsa",   "ecdsa.SignASN1()"),
    (r'\belliptic\.P256\s*\(',        "crypto/elliptic","elliptic.P256()"),
    (r'\belliptic\.P384\s*\(',        "crypto/elliptic","elliptic.P384()"),
    (r'\belliptic\.P521\s*\(',        "crypto/elliptic","elliptic.P521()"),
    (r'\bmd5\.New\s*\(',              "crypto/md5",     "md5.New()"),
    (r'\bmd5\.Sum\s*\(',              "crypto/md5",     "md5.Sum()"),
    (r'\bsha1\.New\s*\(',             "crypto/sha1",    "sha1.New()"),
    (r'\bsha1\.Sum\s*\(',             "crypto/sha1",    "sha1.Sum()"),
    (r'\btls\.Config\s*{',            "crypto/tls",     "tls.Config{}"),
    (r'MinVersion\s*:\s*tls\.VersionTLS10', "crypto/tls", "tls.VersionTLS10 (deprecated)"),
    (r'MinVersion\s*:\s*tls\.VersionTLS11', "crypto/tls", "tls.VersionTLS11 (deprecated)"),
    (r'\bx509\.ParseCertificate\s*\(', "crypto/tls",   "x509.ParseCertificate()"),
    (r'\bssh\.NewServerConn\s*\(',    "golang.org/x/crypto/ssh", "ssh.NewServerConn()"),
    (r'\bssh\.Dial\s*\(',             "golang.org/x/crypto/ssh", "ssh.Dial()"),
]
