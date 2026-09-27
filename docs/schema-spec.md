# Output JSON Schema Specification (v2.2)

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
  "estimated_effort": "high",
  "rule_id": "RSA-SIGNATURE-001",
  "rule_version": "2026.09.26-d7.1",
  "blocker_codes": ["SIGNATURE_FORMAT", "VERIFIER_SUPPORT"],
  "standard_refs": ["NIST FIPS 204"],
  "priority": {
    "cryptographic_urgency": "high",
    "evidence_strength": "inferred",
    "migration_effort": "high",
    "data_exposure": "unknown",
    "overall_review_priority": "high",
    "basis": ["status=quantum_vulnerable", "confidence=inferred"]
  },
  "decision_trace": { /* DecisionTrace object */ }
}
```

All plans remain advisory in D8: `patch_available` is false and the knowledge-base loader rejects rules that attempt to enable it.

### 2.3 DecisionTrace
Each plan carries a deterministic trace from the source observation to the decision. The identifier excludes run IDs and timestamps, so equivalent pinned input and rule versions produce the same trace ID.

```json
{
  "trace_id": "34d18cc648d14dd2",
  "finding_id": "e3b0c44298fc",
  "outcome": "recommend",
  "source_ref": {"file_path": "auth/signer.py", "line_number": 4, "column": 0, "source_commit": "..."},
  "steps": [
    {"stage": "detection", "result": "observed", "explanation": "...", "facts": {}},
    {"stage": "role_inference", "result": "resolved", "explanation": "...", "facts": {}},
    {"stage": "rule_match", "result": "matched", "explanation": "...", "facts": {}},
    {"stage": "blocker_assessment", "result": "blocked", "explanation": "...", "facts": {}},
    {"stage": "decision", "result": "recommend", "explanation": "...", "facts": {}}
  ],
  "unresolved_fields": ["protocol_context"]
}
```

The trace does not duplicate source snippets. It carries the source span, typed facts, rule version, blocker codes and decision. `unresolved_fields` makes missing semantics explicit.

### 2.4 Multi-axis priority
Priority is categorical and explainable. It is not a calibrated probability or a scalar risk score:

- `cryptographic_urgency` derives from the finding security status.
- `evidence_strength` preserves the direct/inferred/ambiguous confidence class.
- `migration_effort` comes from the matched versioned rule.
- `data_exposure` stays `unknown` because the scanner does not infer business sensitivity or retention.
- `overall_review_priority` is `manual_review` for abstentions; otherwise it follows cryptographic urgency.

### 2.5 AssuranceRecord
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
