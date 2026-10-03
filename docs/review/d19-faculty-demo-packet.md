# D19 — Faculty demo packet

## Ten-minute route

### 0:00–1:00 — Problem and boundary

PQMigrate does not equate an import with an operation. It statically gathers evidence, infers a bounded role, recommends or abstains, and keeps source mutation disabled.

### 1:00–2:00 — Reproducible gate

Run `bash scripts/validate_d0_d20.sh`. Explain that scanner exit code 1 means vulnerable cryptography was found, not that execution crashed.

### 2:00–3:00 — Three-fixture scan

Open `review-artifacts/latest/three-fixture-report.json`: three files, four findings, signature and key-transport recommendations, and one import-only abstention.

### 3:00–4:00 — Decision trace

Show finding ID, source span, rule ID/version, five-stage decision trace, blockers and multi-axis priority. Unknown business exposure remains unknown.

### 4:00–5:00 — Preview safety

Show `d12-preview.diff`. It is an exact hash-bound AST preview of one direct MD5 call. Automatic mutation remains disabled.

### 5:00–6:00 — Disposable verification

Show `d13-verification.json`: syntax and AST rescan pass in a disposable copy; original hash and cleanup are verified. This is not semantic proof or a container sandbox.

### 6:00–7:00 — Interoperability

Show `d14-interoperability.json`: six controlled digest scenarios and visible mismatches. This is not PQC/hybrid TLS interoperability.

### 7:00–8:00 — Baselines and ablations

Show `d18-baselines.json`: primitive lookup, AST-only, no-secret-flow, no-context and full pipeline use the same 72 cases. The benchmark is a single-author synthetic Python RSA pilot, not product-wide accuracy.

### 8:00–9:00 — Dashboard and website

Open `http://127.0.0.1:8765` and `http://127.0.0.1:4173`. Trace one finding through evidence, recommendation, refusal/preview, checks and export.

### 9:00–10:00 — Limits and next study

State the remaining gaps: independent annotation, cross-file analysis, real PQC/hybrid interop, provider-specific constructions, complete browser/backend deployment testing and external format ingestion.

## Recovery route

If a live command fails, use saved JSON artifacts and logs. Never hide a failed or `not_run` state. Do not create or claim a v0.1 tag until D20 is green, the worktree is reviewed and the intended release commit is pushed.
