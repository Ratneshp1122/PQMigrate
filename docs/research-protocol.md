# Research Protocol & Taxonomies

**Scope:** Open-source Python (AST-based) and Go (AST-based) codebases.

## 1. Core Taxonomies

### 1.1 Cryptographic Role Taxonomy
What structural part of the cryptographic architecture does this primitive fulfill?
- `signature`
- `key_establishment`
- `key_transport`
- `encryption` (symmetric/asymmetric)
- `authentication`
- `hash`
- `mac`
- `certificate_identity`
- `unknown`

### 1.2 Operation Taxonomy
What exact action is happening at the localized AST node?
- `sign`
- `verify`
- `encrypt`
- `decrypt`
- `generate`
- `exchange`
- `encapsulate`
- `decapsulate`
- `configure`
- `unknown`

### 1.3 Status & Confidence Taxonomy
- **Status:** `quantum_vulnerable`, `quantum_security_reduced` (Grover), `standardized_pqc`, `context_dependent`, `deprecated_classically`, `unknown`.
- **Confidence:** 
  - `direct` (e.g., `pkcs1_15.new(rsa_key).sign(hash)`)
  - `inferred` (e.g., passing a generic `key` object to `x509.CertificateBuilder`)
  - `ambiguous` (e.g., `import rsa`)

---

## 2. Labeler Calibration: 10 Hand-Worked Examples

These manual examples serve as the pass-gate for Day 1. They map raw source code to our typed `CryptoIR` specification.

### Example 1: Clear RSA Signature
```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
# ... 
signature = private_key.sign(data, padding.PSS(...))
```
- **Pattern:** `cryptography.hazmat.primitives.asymmetric.rsa`
- **Role:** `signature`
- **Operation:** `sign`
- **Status:** `quantum_vulnerable`
- **Confidence:** `direct`
- **Target:** ML-DSA

### Example 2: Clear RSA Encryption (Key Transport)
```python
ciphertext = public_key.encrypt(session_key, padding.OAEP(...))
```
- **Pattern:** `cryptography.hazmat.primitives.asymmetric.rsa`
- **Role:** `key_transport`
- **Operation:** `encrypt`
- **Status:** `quantum_vulnerable` (HNDL)
- **Confidence:** `direct`
- **Target:** ML-KEM

### Example 3: Ambiguous Import
```python
import rsa
```
- **Pattern:** `import rsa`
- **Role:** `unknown`
- **Operation:** `unknown`
- **Status:** `quantum_vulnerable`
- **Confidence:** `ambiguous` (Abstain from patching, output `inventory_lead`)

### Example 4: Go ECDSA Generation
```go
priv, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
```
- **Pattern:** `crypto/ecdsa`
- **Role:** `signature` (Inherent to ECDSA)
- **Operation:** `generate`
- **Status:** `quantum_vulnerable`
- **Confidence:** `direct`
- **Target:** ML-DSA

### Example 5: Go ECDH Key Exchange
```go
curve := ecdh.X25519()
priv, _ := curve.GenerateKey(rand.Reader)
```
- **Pattern:** `crypto/ecdh`
- **Role:** `key_establishment`
- **Operation:** `generate`
- **Status:** `quantum_vulnerable` (HNDL)
- **Confidence:** `direct`
- **Target:** X25519 + ML-KEM (RFC 10024 hybrid)

### Example 6: Hardcoded TLS Protocol Configuration
```python
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
```
- **Pattern:** `ssl.PROTOCOL_TLSv1_2`
- **Role:** `key_establishment` (Contextual via TLS)
- **Operation:** `configure`
- **Status:** `context_dependent` (Relies on cipher suite negotiation)
- **Confidence:** `direct`
- **Target:** Warn/Advise to ensure TLS 1.3 + RFC 10024 groups.

### Example 7: SHA-256 Hashing
```python
import hashlib
digest = hashlib.sha256(data).digest()
```
- **Pattern:** `hashlib.sha256`
- **Role:** `hash`
- **Operation:** `hash`
- **Status:** `quantum_security_reduced` (Grover vulnerability halves bits)
- **Confidence:** `direct`
- **Target:** SHA-384 / SHA-512 (if 256-bit PQ security is required).

### Example 8: Go Ed25519 Verification
```go
valid := ed25519.Verify(pubKey, message, signature)
```
- **Pattern:** `golang.org/x/crypto/ed25519`
- **Role:** `signature`
- **Operation:** `verify`
- **Status:** `quantum_vulnerable`
- **Confidence:** `direct`
- **Target:** ML-DSA

### Example 9: Inferred JWT Signing
```python
import jwt
token = jwt.encode(payload, private_key, algorithm="RS256")
```
- **Pattern:** `RS256` (String literal pattern)
- **Role:** `signature`
- **Operation:** `sign`
- **Status:** `quantum_vulnerable`
- **Confidence:** `inferred` (Requires tracing string literals into JWT wrappers)
- **Target:** MLDSA (via hybrid JWT extensions, or abstain if standard unsupported).

### Example 10: AES-GCM Symmetric Encryption
```go
block, _ := aes.NewCipher(key) // 16 byte key
aesgcm, _ := cipher.NewGCM(block)
aesgcm.Seal(nil, nonce, plaintext, nil)
```
- **Pattern:** `crypto/aes`
- **Role:** `encryption`
- **Operation:** `encrypt`
- **Status:** `quantum_security_reduced` (AES-128 drops to ~64 bits via Grover)
- **Confidence:** `direct`
- **Target:** Key rotation to AES-256.
