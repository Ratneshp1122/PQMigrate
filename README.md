# 🛡️ PQMigrate: Post-Quantum Cryptography Migration Tool

[![NIST FIPS](https://img.shields.io/badge/NIST-FIPS_203%20%7C%20204%20%7C%20205-blue.svg)](https://csrc.nist.gov/projects/post-quantum-cryptography)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/Dashboard-React_18-61dafb.svg)](https://reactjs.org)

**PQMigrate** is a research prototype for AST-aware cryptographic inventory and evidence-linked post-quantum migration planning.

The current Python path uses bounded AST dataflow to distinguish selected RSA signing and key-transport cases from unresolved imports. A versioned YAML knowledge base produces advisory plans with blocker codes and standards references. The planner abstains when evidence is missing or conflicting and does not treat role inference as authorization to patch.

---

## ✨ Key Capabilities

1. **AST discovery (`/scanner`)**: Detects supported Python operations and inventory leads. Go support remains regex-based.
2. **Bounded role inference (`/resolver`)**: Links selected same-scope RSA key uses and explicitly abstains on unrelated, absent, or conflicting evidence.
3. **Versioned rule planning (`/knowledge`)**: Loads validated YAML rules with rule IDs, blocker codes, standards references, and advisory-only decisions.
4. **Assurance interface (`/backend` and `/frontend`)**: Stores and displays scan evidence. The CLI remains the primary verified review path.
5. **Pilot evaluation (`/benchmarks`)**: Runs a versioned 72-case synthetic Python RSA benchmark with held-out splits, raw predictions, metrics, and error cases.

---

## 🏗️ Architecture Pipeline

```mermaid
graph LR
    A[Source Code] --> B[AST Scanner]
    B --> C[Bounded Role Resolver]
    C --> D[YAML Rule Planner]
    D --> E[JSON Schema 2.2]
    E --> F[CLI or React Dashboard]
```

---

## 🚀 Quick Start (Demo Script)

### 1. Installation
```bash
git clone https://github.com/Ratneshp1122/PQMigrate.git
cd PQMigrate
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate a Migration Plan
Scan a target directory and export a standards-referenced advisory plan:
```bash
python3 cli.py scan demo/ --format json --output report_v2.json
```

### 3. Launch the Assurance Dashboard
Spin up the visual dashboard to review vulnerabilities and abstentions:
```bash
python3 -m http.server 8080
# Open http://localhost:8080/dashboard/index.html in your browser
```

### 4. Run the review smoke suite
Run the Python tests, Maven tests, frontend build, and controlled three-fixture scan:
```bash
scripts/review_smoke.sh
```

### 5. Run the D9 pilot benchmark

```bash
scripts/run_benchmark.sh
```

The generated metrics apply only to the committed single-author synthetic Python RSA pilot. They are not product-wide or publication-quality accuracy claims.

---

## 📜 Supported Cryptographic Mappings

| Legacy Primitive | Vulnerability | NIST PQC Standard Target | Role |
| :--- | :--- | :--- | :--- |
| **RSA / ECDH** | Shor's Algorithm | **FIPS 203 (ML-KEM)** / RFC 10024 | Key Encapsulation |
| **RSA / ECDSA** | Shor's Algorithm | **FIPS 204 (ML-DSA)** | Digital Signatures |
| **AES-128** | Grover's Algorithm | **AES-256** | Symmetric Encryption |
| **SHA-1 / MD5** | Collision Attacks | **SHA-256 / SHA-3** | Hashing |

---

## 🛑 Architectural Decision Records (ADRs)

* **ADR-001 (Semantic Abstention):** If the analyzer cannot link a primitive to a supported role, the planner emits an abstention with explicit blocker codes.
* **D7 rule safety:** The YAML loader rejects duplicate rule IDs, unsupported role names, missing provenance fields, and any D7 rule that enables automatic patching.

---
*Developed for advanced cryptographic modernization workflows.*
