# PQMigrate: Evidence-Driven and Abstention-Aware Planning for Post-Quantum Cryptographic Migration

> Internal draft scaffold — 4 October 2026. Bracketed text is unfinished and must not be presented as a result.

## Abstract

Migrating software to post-quantum cryptography requires more than locating cryptographic names: the same primitive may implement signatures, general encryption, key transport, or protocol-specific behavior with different migration constraints. We present PQMigrate, a bounded static-analysis and planning system that links source evidence to operation roles, versioned migration knowledge, explicit blockers, and an abstention outcome when required context is unresolved. The current implementation analyzes Python and Go, emits traceable JSON, SARIF, and CycloneDX CBOM evidence, and enforces a fail-closed mutation policy. On a 72-case single-author synthetic Python RSA pilot, the full bounded pipeline achieved operation-detection precision 1.00, recall 0.769, and F1 0.870, while answering 40 of 52 gold operations with 1.00 role accuracy among answered cases. These preliminary figures are not product-wide accuracy results. [Replace or supplement with the independently annotated repository-separated evaluation before external submission.] Our results motivate evaluating migration planners using both answer coverage and unsafe-recommendation rate rather than detection accuracy alone.

## 1. Introduction

[Draft the quantum-migration motivation, inventory-versus-planning gap, and concrete example showing why RSA signature and key transport need different plans.]

### Contributions

1. A typed, evidence-linked intermediate representation for cryptographic observations, operation roles and migration decisions.
2. Bounded Python and Go semantic inference that distinguishes confirmed operations from inventory leads and explicitly abstains on unsupported or conflicting evidence.
3. A versioned migration knowledge base and deterministic decision trace with blocker-aware, fail-closed patch eligibility.
4. A reproducible evaluation framework with same-corpus baselines, feature ablations, raw failure accounting and standards-based exports.

## 2. Research questions

- RQ1: How accurately does bounded semantic analysis distinguish operations from inventory-only evidence?
- RQ2: How accurately does it resolve migration-relevant roles?
- RQ3: What is the contribution of identity flow, session-secret evidence and protocol context?
- RQ4: How does abstention trade coverage for fewer unsafe recommendations?
- RQ5: Are decisions traceable and reproducible at an exact source commit?

## 3. Related work

[Cover Cryptoscope, CBOM, cryptographic API misuse analysis, CamBench, static data-flow analysis, crypto agility and standards-guided PQC migration.]

## 4. System design

### 4.1 Threat model and scope

PQMigrate treats scanned repositories as untrusted input and does not execute target source during analysis. Its bounded inference is not whole-program proof. Unknown identity, role, compatibility, tests or authorization causes abstention or patch refusal.

### 4.2 Evidence pipeline

[Describe discovery → semantic inference → CryptoIR → knowledge base → planner → trace/export.]

### 4.3 Abstention and patch policy

Patch eligibility requires known role, supported construction, interoperability evidence, adequate tests and explicit operator authorization. Any false or unknown condition refuses mutation. The current paper evaluates planning and preview evidence; it does not claim automatic PQC transformation.

## 5. Dataset and annotation methodology

[Insert the frozen 200–300-case sampling, repository-separated split, two-annotator protocol, disagreement preservation, adjudication, and Cohen's kappa procedure from the execution plan.]

## 6. Baselines and ablations

- Primitive/import lookup.
- Regex call matching.
- AST method matching.
- Full PQMigrate.
- Pinned Semgrep Community Edition with published rules.
- No-session-secret-flow and no-protocol-context ablations.

All systems use the same cases, labels, denominators, timeouts and failure accounting.

## 7. Preliminary pilot results

| System | Operation F1 | End-to-end role accuracy | Error count |
|---|---:|---:|---:|
| Primitive lookup | 0.741 | 0.000 | 68 |
| AST method only | 0.880 | 0.615 | 24 |
| No session-secret flow | 0.870 | 0.538 | 24 |
| No protocol context | 0.870 | 0.769 | 20 |
| Full pipeline | 0.870 | 0.769 | 12 |

These results use the 72-case single-author synthetic Python RSA pilot. The AST-only baseline has higher operation F1 than the full pipeline, illustrating why detection F1 alone does not measure role correctness or safety. [Replace the main results with repository-cluster bootstrap intervals on the independently annotated corpus.]

## 8. Error analysis

[Report errors by identity resolution, cross-function/cross-file flow, wrappers, secret-source inference, protocol context, parser failure and annotation ambiguity.]

## 9. Discussion

[Discuss the coverage/safety trade-off and when abstention is preferable to an incorrect migration recommendation.]

## 10. Threats to validity

The current pilot is synthetic, single-author, Python/RSA-specific and correlated by scenario family. The implemented analysis is bounded and does not establish whole-program behavior. Standards-valid exports do not prove downstream ingestion, and digest-contract interoperability does not establish ML-KEM, ML-DSA, TLS or production compatibility.

## 11. Reproducibility

The D0–D20 gate passed twice from clean commit `bcfb5e40fbc8eb74e1c919114f54031d03ab44e9`. Complete logs, generated artifacts and checksums are preserved separately from the source commit. [Add public release URL and `v0.1.0` tag after faculty/security approval.]

## 12. Conclusion

[Conclude only that evidence-linked, abstention-aware planning is feasible and measurable within the evaluated scope.]

## References

[Convert the verified bibliography to the required IEEE or venue format.]
