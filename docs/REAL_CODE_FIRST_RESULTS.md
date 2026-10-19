# First real-code scan results — 6 October 2026

The first batch has completed on six public repositories using unchanged PQMigrate implementation commit `bcfb5e40fbc8eb74e1c919114f54031d03ab44e9`. Each repository revision, license-file links/hashes, environment, command, log, output and checksum is preserved in the run directory.

| Repository | Scanned files | Finding records | Known-role records |
|---|---:|---:|---:|
| jpadilla/pyjwt | 26 | 15 | 0 |
| paramiko/paramiko | 70 | 17 | 0 |
| pyca/cryptography | 243 | 115 | 2 |
| golang-jwt/jwt | 46 | 13 | 0 |
| go-jose/go-jose | 73 | 63 | 0 |
| golang/crypto | 328 | 220 | 2 |
| Total | 786 | 443 | 4 |

The four known roles comprise two hash records, one RSA signature record in a test file, and one RSA encryption record. The other 439 records have unknown role. These are record counts, not unique-operation counts, correctness estimates, or recall. Duplicate leads and import-location records require manual operation delimitation before evaluation.

There were six successful scan/report runs, no scan timeouts, and no independently observed syntax failures among the 786 eligible files. Five additional Python files in pyca/cryptography were excluded by scanner selection policy. This does not assess unsupported languages or all project assets. The separate parser ledger is necessary because the frozen scanner can omit failures from its own JSON.

Planner traces contain 440 `abstain` outcomes and three `recommend` outcomes. No record has `patch_available=true`. These are observed planner outcomes on discovered records; no independent advisory labels exist to judge whether each recommendation or abstention is appropriate.

## Inspected examples motivating further work

These observations are a small analyst inspection, not adjudicated gold labels:

- PyJWT's [RSA sign/verify implementation](https://github.com/jpadilla/pyjwt/blob/b5bd6fe6d7ac0370ba90557c7a1e3d50a9414572/jwt/algorithms.py#L682) receives a typed RSA key as a function parameter. This differs from the pilot's locally generated-key pattern; the scan's role records remain unknown.
- Paramiko's [SSH signing function](https://github.com/paramiko/paramiko/blob/142f593e40ad767c5e3556cbace66dc84589620c/paramiko/rsakey.py#L134) invokes `self.key.sign`. Object-field provenance is needed to resolve this pattern reliably; the scan's role records remain unknown.
- Go JWT's [RSA signing implementation](https://github.com/golang-jwt/jwt/blob/73c870b18e68b6e654b2b03f485aa3c9fab32cea/rsa.go#L70) obtains an RSA key through a type assertion and calls `rsa.SignPKCS1v15`; the scan's role records remain unknown.
- One pyca/cryptography SHA-512 record is labeled `standardized_pqc` by the frozen tool. This category assignment needs review: a hash function's presence alone is not evidence of completed PQC migration. Preserve this output when evaluating status-label quality.

The batch exposes a coverage gap that the 72 synthetic cases did not measure. It should motivate bounded support for common parameter, member-field and type-assertion patterns, with negative cases for shadowing, incompatible types and conflicting evidence. Do not tune on these repositories and later call them unseen test data.

## Prepared evaluation material

There are 240 unreviewed source anchors, 40 per repository: 144 selected through separate text search, 48 through scanner findings, and 48 from ordinary source. Ordinary-source anchors are candidate controls; they are not assumed negative. Exact snippet hashes have no duplicate groups, but overlapping snippets and semantically related code still require curation.

`annotator-a.jsonl` and `annotator-b.jsonl` are separate blank review packets; tool predictions are retained separately. Neither packet counts as completed annotation. Reviewers must delimit actual operations and inspect broader context, then label independently. Disagreement records, adjudication and agreement statistics follow the human review.

The 72-case synthetic study remains regression evidence. This new material is exploratory real-code evidence. Independently adjudicated cases, common baseline runs and unseen repository families are required to support real-code accuracy claims.

## Saved locations

- WSL results: `/home/ratneshp0411/pqc_migration_tool/review-artifacts/real-code/2026-10-06-run1/`
- WSL runner: `/home/ratneshp0411/pqc_migration_tool/experiments/real_code_study.py`
- WSL guide: `/home/ratneshp0411/pqc_migration_tool/docs/REAL_CODE_STUDY.md`
- Frozen scanner and target checkouts: `/home/ratneshp0411/pqmigrate-real-code-study/`
- Windows evidence mirror: `D:\New folder (6)\pqmigrate-real-code-study\evidence\2026-10-06-run1\`

The validation script verified 44 checksummed evidence files, target revisions, hashes of audited source files, record counts, and all 240 blank annotation entries in each reviewer packet. This was a scan-specific validation, not a new run of the entire D0-D20 gate.
