# PQMigrate panel questions and concise answers

## Why can RSA not map directly to ML-KEM?

RSA can support signatures or encryption. ML-KEM establishes shared secrets, while ML-DSA provides signatures. PQMigrate first links the key to an operation and abstains when the role remains unknown.

## Is this an AI model?

The current system is deterministic rule-based static analysis. It produces evidence traces and explicit abstentions. No trained model or probabilistic accuracy claim is used.

## What changed beyond primitive matching?

The current Python path links a generated RSA key to selected same-scope consumers. It distinguishes JWT signing, generated-session-key transport, import-only leads, unrelated keys, and conflicting roles.

## Does the tool safely patch RSA code now?

No. Role inference supplies advice, but it does not establish provider support, peer interoperability, test adequacy, or operator authorization. The planner therefore keeps `patch_available=false` for the review cases.

## What mathematically prevents an unknown condition from enabling a patch?

The D11 gate uses five independent three-valued conditions: known role, supported construction, interoperable peers, tests, and operator authorization. Eligibility requires all five to be true. The exhaustive test evaluates all 243 assignments; 242 are refused and only the all-true vector is theoretically eligible. Current reports cannot supply four trusted conditions, so no mutation is enabled.

## Does passing pytest prove migration safety?

No. It proves only the specified checks in that environment. Protocol interoperability, certificate formats, external consumers, deployment configuration, and unsupported paths remain separate conditions.

## How do you control false positives?

The analyzer requires identity-linked use of the tracked key, includes negative fixtures, abstains on conflicting roles, and keeps imports separate from confirmed operations. The D9 synthetic pilot reports operation precision/recall/F1, role accuracy among answered cases, answer coverage, raw predictions, and errors. Independent labels and real-project cases are still required.

## What are the present limitations?

Python role inference covers a deliberately narrow RSA subset. Go detection remains regex-based. D9 exposes false negatives for parameter and alias flows. No transformation is approved. Independent benchmark adjudication, downstream-platform export integration, isolated patch verification, and interoperability remain future milestones.

## Can other security tools consume the result?

PQMigrate emits SARIF 2.1.0 for code-scanning workflows and CycloneDX 1.7 CBOM for cryptographic inventory. Each document is validated against a pinned official schema before writing. D10 proves local schema conformance and traceable field mapping, not successful import into every downstream product.

## What do the D9 numbers prove?

Only behavior on 68 evaluated cases in a 72-case, single-author synthetic Python RSA pilot; four parse failures are reported separately. They do not establish repository-level or product-wide accuracy. The useful D9 result is reproducible raw predictions and visible coverage gaps, not a publication claim.

## Why keep the Spring and React applications?

They provide authenticated orchestration and evidence inspection. The Python engine remains the source of cryptographic semantics. The research claim depends on correct evidence and measured evaluation, not UI complexity.

## What prevents one user from reading another user's scan?

Scan list, detail, and delete operations resolve the authenticated email to a user ID and query by both scan ID and owner. Unit tests cover cross-user rejection. Dashboard aggregates need the same owner-scoping before a multi-user production claim.

## Where is the research novelty?

The planned evaluation tests whether role-aware planning and calibrated abstention improve on primitive inventories and simpler static baselines. Novelty will be supported by comparative measurements, not by the existence of YAML rules or a dashboard.
