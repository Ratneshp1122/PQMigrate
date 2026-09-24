# Threat Model & Security Scope

## 1. Cryptographic Threat Environment
The primary driver for PQC migration is the advent of Cryptographically Relevant Quantum Computers (CRQCs) running Shor's and Grover's algorithms.

### 1.1 Harvest Now, Decrypt Later (HNDL)
- **Target:** Key Exchange (DH, ECDH, RSA-KEM, X25519) and Public Key Encryption (RSA-OAEP).
- **Impact:** CRITICAL. Adversaries record ciphertext traffic today. When CRQCs are available, they will retroactively decrypt the traffic.
- **Migration Urgency:** Immediate. HNDL directly threatens data with long-term confidentiality requirements.

### 1.2 Quantum Forgery
- **Target:** Digital Signatures (RSA, ECDSA, Ed25519).
- **Impact:** CRITICAL (but non-retroactive). A CRQC can forge signatures for updates, authenticate as any user, or issue fake certificates.
- **Migration Urgency:** Dependent on hardware lifecycle and root-of-trust expiry. Not vulnerable to HNDL.

### 1.3 Grover's Quantum Search
- **Target:** Symmetric Encryption (AES) and Hash Functions (SHA-2, SHA-3).
- **Impact:** MEDIUM (Quantum Security Reduced). Grover's algorithm halves the effective bit-strength (e.g., AES-128 drops to 64-bit security).
- **Migration Strategy:** Key size doubling (e.g., AES-128 → AES-256, SHA-256 → SHA-384).

## 2. Tool Operator Threat Model
The `pqc_migration_tool` operates on arbitrary, untrusted source code.

### 2.1 Threat: Malicious Repositories
- **Vector:** The tool scans downloaded or third-party repositories. If the tool executes code to determine behavior (e.g., `import`ing modules dynamically), a malicious repository could execute arbitrary code on the analyst's machine.
- **Mitigation:** **Static Analysis Only.** The tool uses AST (Abstract Syntax Tree) and regex parsing. We explicitly forbid `eval()`, `exec()`, or dynamic module loading.

### 2.2 Threat: Automated Patch Failure
- **Vector:** The tool recommends or implements a PQC migration that breaks cryptographic backward compatibility, invalidates database signatures, or applies the wrong algorithm (e.g., ML-DSA to an encryption context).
- **Mitigation:** **Explicit Abstention.** The tool must explicitly classify its confidence (`direct`, `inferred`, `ambiguous`). If confidence is ambiguous, the tool must `abstain` from automated patching and output an `inventory_lead` flag for manual redesign.
