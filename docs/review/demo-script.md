# Eight-minute PQMigrate review demo

## Pre-demo setup

```bash
cd /home/ratneshp0411/pqc_migration_tool
git status --short --branch
git rev-parse --short HEAD
```

Keep `review-artifacts/latest/three-fixture-report.json` available as the backup result.

## 0:00–0:50 — Problem

Explain that an RSA name does not identify its purpose. The migration family depends on whether the key signs data, transports a secret, or has no observed consumer.

## 0:50–1:35 — Verified scope

Show `docs/review-evidence.md`. State the exact Python and Maven test counts. Describe Go support as regex-based. Do not claim benchmark accuracy, safe general patching, or completed interoperability.

## 1:35–2:35 — SRS boundary

Point to FR-01 through FR-07 in the review packet. Emphasize `UNKNOWN`, evidence traceability, versioned reports, and failed-worker handling.

## 2:35–3:35 — Algorithm and model

Open `docs/review/algorithm-and-model.md`. Explain the role function and the five-condition eligibility conjunction. State that the current planner keeps `patch_available=false` because inference does not prove deployment readiness.

## 3:35–4:25 — Architecture and data flow

Open `docs/review/system-diagrams.md`. Trace source enumeration, AST discovery, bounded role inference, advisory planning, and JSON output. Distinguish the CLI evidence path from the optional Spring/React interface.

## 4:25–6:45 — Live fixture scan

```bash
python3 cli.py scan tests/fixtures/review \
  --format json \
  --output /tmp/pqmigrate-review-live.json
```

Exit code 1 is expected because the policy found vulnerable cryptography. Show these records:

1. JWT fixture: role `signature`, protocol `jwt`, evidence at `jwt.encode`, ML-DSA assessment, no automatic patch.
2. Key-transport fixture: role `key_transport`, evidence linking `os.urandom` to RSA encryption, KEM/DEM redesign assessment, no automatic patch.
3. Import-only fixture: role `unknown`, `import_lead`, explicit abstention.

## 6:45–7:25 — Negative evidence

```bash
cd /home/ratneshp0411
python3 -m pytest -q pqc_migration_tool/tests/test_context_inference.py
```

Mention the unrelated-key and conflicting-role tests. These prevent proximity-only inference.

## 7:25–8:00 — Next measured milestones

State that the next milestones are the versioned knowledge base, pilot benchmark, standard exports, and isolated migration assurance. Ask the reviewer to confirm the ground-truth labelling rules and the contexts that deserve priority.

## Failure fallback

If the live command fails, show the preserved JSON report and smoke logs. Do not switch to seeded dashboard data and describe it as a fresh scan.
