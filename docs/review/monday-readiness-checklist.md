# Monday review readiness checklist

## Repository freeze

- [ ] `git status` shows only intentional review changes before commit.
- [ ] Record the final commit SHA in `review-artifacts/latest/baseline-metadata.log`.
- [ ] Do not push unrelated feature work into the review commit.

## Automated evidence

- [ ] Run `scripts/review_smoke.sh` from WSL.
- [ ] Confirm all Python tests pass.
- [ ] Confirm all Maven tests pass and the test count is nonzero.
- [ ] Confirm the frontend production build passes.
- [ ] Confirm the three-fixture report contains signature, key-transport, and unknown results.
- [ ] Confirm every fixture plan has `patch_available=false`.
- [ ] Confirm the D9 result has 72 raw predictions, held-out split metrics, and visible error cases.
- [ ] Confirm the SARIF 2.1.0 and CycloneDX 1.7 artifacts pass offline schema validation.

## Review documents

- [ ] SRS wording matches the current code and labels later milestones as planned.
- [ ] Algorithm/model handout matches the bounded analyzer.
- [ ] Mermaid diagrams distinguish the current CLI path from future work.
- [ ] Demo script and panel Q&A are available offline.

## Live demonstration

- [ ] Rehearse the eight-minute CLI flow once without interruption.
- [ ] Keep the preserved JSON and raw logs open as fallback.
- [ ] Keep `three-fixture.sarif.json` and `three-fixture.cdx.json` available as interoperability evidence.
- [ ] Show the final commit SHA before the scan.
- [ ] Explain that scanner exit code 1 means findings were detected.
- [ ] Do not call the Spring dashboard end-to-end verified unless a separate smoke test succeeds.

## Claim control

- [ ] Qualify every D9 metric as a single-author synthetic Python RSA pilot result.
- [ ] Do not claim independent, repository-level, Go, or product-wide benchmark accuracy.
- [ ] Do not call an import a confirmed operation.
- [ ] Do not describe role inference as patch authorization.
- [ ] Do not claim Go AST resolution.
- [ ] Describe SARIF/CBOM as schema-validated local exports; do not claim a third-party import that was not tested.
- [ ] Label interoperability and general patch assurance as planned.
