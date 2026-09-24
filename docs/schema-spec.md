# Output JSON Schema Specification

## 1. Overview
The PQC Migration Tool generates a structured JSON output utilizing the `ProjectReport` root object. This output is designed to be directly ingested by the React/TypeScript dashboard defined in the research roadmap.

## 2. Core Entities

### 2.1 CryptoIR (Cryptographic Internal Representation)
Represents a single, semantically resolved cryptographic operation found in the source code.

```json
{
  "id": "e3b0c44298fc1c149afbf4c8996fb924",
  "primitive_name": "crypto/rsa",
  "location": {
    "file_path": "auth/signer.go",
    "line_number": 42,
    "column": 12,
    "context_snippet": "sig, err := rsa.SignPKCS1v15(rand, priv, hash, hashed)"
  },
  "role": "signature",           // From CryptoRole enum
  "operation": "sign",           // From CryptoOperation enum
  "status": "quantum_vulnerable",// From SecurityStatus enum
  "confidence": "direct",        // From ConfidenceLevel enum
  "detection_type": "operation_candidate"
}
```

### 2.2 MigrationPlan
If a `CryptoIR` is well-understood (e.g., Confidence is `direct` or `inferred`), a MigrationPlan is attached. If confidence is `ambiguous`, the `MigrationPlan` requires manual intervention (abstention).

```json
{
  "target_algorithm": "ML-DSA-65",
  "target_standard": "FIPS 204",
  "patch_available": true,
  "requires_manual_intervention": false,
  "intervention_reason": null,
  "estimated_effort": "low"
}
```

### 2.3 AssuranceRecord
Wraps a finding with its plan, enabling test-driven verification marking.

```json
{
  "finding": { /* CryptoIR object */ },
  "plan": { /* MigrationPlan object, or null */ },
  "tests_passed": false,
  "verified_by_human": false
}
```

## 3. Strict Enums

### CryptoRole
`signature`, `key_establishment`, `key_transport`, `encryption`, `authentication`, `hash`, `mac`, `certificate_identity`, `unknown`

### CryptoOperation
`sign`, `verify`, `encrypt`, `decrypt`, `generate`, `exchange`, `encapsulate`, `decapsulate`, `configure`, `unknown`

### ConfidenceLevel
- `direct`: Semantics proven via immediate AST call structure (e.g., `.encrypt()`).
- `inferred`: Semantics deduced via dataflow (e.g., variable passed into known sink).
- `ambiguous`: Semantics unknown (e.g., bare `import` statement). Forces abstention.
