# D20 — Integration and release gate

D20 is the post-roadmap integration milestone. The original plan ended at D19; D20 exists to make the accumulated implementation reproducible as one ordered chain.

`bash scripts/validate_d0_d20.sh` runs the strict D0–D11 gate, D12 preview, D13 disposable verification, D14/D15 lab and dashboard checks, D16 assurance dashboard, D17 website, D18 baselines/ablations and D19 packet/readiness audit. It stops on the first failure and only then writes `review-artifacts/latest/d20-integration-summary.json` with hashes of every milestone artifact.

D20 makes D17 synchronize its static sample from the freshly regenerated canonical manifest before testing. This preserves exact scan UUID, source commit, counts and decisions while allowing repeated validation without manual edits or stale provenance.

A D20 pass is not a production deployment or security certification. The CLI is validated in WSL, D15/D16 is loopback-only, D17 is a local static preview, Spring is test-only, React is build-only, automatic mutation remains disabled, and no Git tag is created by the gate.
