# D0 Baseline Audit

**Date:** 24 September 2026
**Baseline Commit:** `11dbc71` (Root commit mapping to end-of-sprint Day 5)
**Environment:** WSL Kali Linux (x86_64), Python 3.13.12, cryptography 50.0.0

## 1. Objective
Per the Research & Engineering Execution Plan, Day 0 serves as a strict verification checkpoint. The objective is to freeze the initial "Scanner" prototype, capture reproducible test and scan logs, audit the registry for precision, and explicitly cancel unsafe prior assumptions before moving into semantic analysis (D1-D5).

## 2. Artifacts Captured
All raw logs are stored in `docs/scan-logs/`:
- `test-baseline.txt`: 23/23 tests passed.
- `pip-freeze-baseline.txt`: Pinned Python dependencies.
- `scan-paramiko-console.txt` & `.json`: Baseline scan of `paramiko/paramiko`.
- `scan-requests-console.txt` & `.json`: Baseline scan of `psf/requests`.
- `scan-vault-console.txt` & `.json`: Baseline scan of `hashicorp/vault`.
- `registry-audit-full.json` & `d0-audit-output.txt`: Classification of all 91 regex/AST patterns.

## 3. Baseline Scan Reproduction Results

| Repository | Files Scanned | System Risk Score | Compliance Grade |
|---|---|---|---|
| `paramiko/paramiko` | 70 | 97.6 | F — Immediate action required |
| `psf/requests` | 37 | 84.3 | D — High priority migration needed |
| `hashicorp/vault` | 2381 | 89.4 | F — Immediate action required |

*Note: The current JSON export schema drops top-level integer counts (CRITICAL, HIGH, etc.) in favor of raw finding arrays. This is noted for the schema upgrade in D2.*

## 4. Registry Classification Audit
The registry contains **91 total entries** (44 Python, 47 Go).
We audited the registry to determine how many patterns represent an actual cryptographic *operation* versus a mere *import lead*.

- **Configuration Leads (4):** TLS/SSL protocol flag accesses.
- **Operation Candidates (29):** Patterns tied to a verb (`sign`, `encrypt`, `GenerateKey`, etc.).
- **Import Leads (58):** General module/package imports with no specific operation.

**Critical Finding:** 17 of the `import_lead` patterns are marked as `CRITICAL`.
*Conclusion:* The scanner currently flags an entire file as CRITICAL simply for containing `import rsa` or `import "crypto/rsa"`. This cannot safely drive an automated patch without high false-positive risk.

## 5. Security & Scope Policy Adjustments (Enforced)

Based on the research roadmap, the following prior sprint goals are **CANCELLED** and explicitly disabled going forward:

1. **Direct RSA → ML-KEM rewrites:** Canceled. RSA can represent signing, encryption, or protocol identity. An algorithm name cannot determine a safe rewrite.
2. **Handwritten HKDF(X25519 \|\| ML-KEM) combiners:** Canceled as a migration recommendation. TLS 1.3 hybrid key agreement must use implementations of standardized groups in RFC 10024.
3. **Single Letter Grades:** Canceled. Replacing "Grade F" with an independent, multidimensional priority model in upcoming milestones.

## 6. Known Bugs & Refactoring Ledger

| ID | Severity | Description | Required Fix Milestone |
|---|---|---|---|
| BUG-01 | CRITICAL | Import patterns flagged as CRITICAL without operation proof. | D3 (Python Resolver), D4 (Go AST) |
| BUG-02 | CRITICAL | Single risk score collapses evidence; untraceable. | D8 (Planner / Priority) |
| BUG-03 | CRITICAL | Dangerous patch rules (RSA to ML-KEM generic rewrite). | D11 (Patch Policy constraint) |
| BUG-04 | CRITICAL | Non-standard hybrid combiner recommended. | D11 (Patch Policy constraint) |
| BUG-05 | MEDIUM | Deduplication by primitive drops 2nd distinct usage in same file. | D2 (Typed CryptoIR) |
| BUG-06 | MEDIUM | SHA-256 labeled SAFE globally rather than quantum-reduced. | D2 (Typed CryptoIR status enum) |
| BUG-07 | LOW | Skipped/vendored files not recorded in output schema. | D10 (Output Contract) |
| BUG-08 | LOW | Parser failures silently skipped. | D10 (Output Contract) |

## 7. Conclusion
Gate D0 is **PASSED**. The current tool establishes a reliable, fast baseline inventory but lacks the semantic awareness necessary for safe patching. Proceed to D1: Research Protocol & Threat Modeling.
