# PQMigrate D0–D11 reproduction and validation guide

This is the authoritative commit-level implementation check. It validates the declared bounded D0–D11 scope, preserves raw outputs, and rejects missing scope instead of converting it into a claim.

## Current acceptance result

All twelve milestones pass their declared bounded acceptance checks. D4 now combines regex inventory discovery with Tree-sitter Go parsing and alias-aware, same-function RSA role inference. The accurate status is `PASS`; this does not imply general interprocedural Go understanding or safe automatic migration.

| Day | Result | What is reproduced |
|---|---|---|
| D0 | Pass | Historical baseline documents plus a fresh registry-classification audit |
| D1 | Pass | Research protocol, threat model, and abstention scope decision |
| D2 | Pass | Typed CryptoIR/report models, JSON round trips, enum behavior |
| D3 | Pass | Bounded Python AST role analysis |
| D4 | Pass, bounded | Tree-sitter Go parser plus alias-aware, same-function RSA role inference and fail-closed negative cases |
| D5 | Pass | Same-scope RSA key-use flow and negative/conflict fixtures |
| D6 | Pass | Linked JWT context inference and explicit unknown states |
| D7 | Pass | Nine versioned YAML rules and loader rejection tests |
| D8 | Pass | Five-stage decision trace, deterministic IDs, priority axes |
| D9 | Pass, bounded | 72-case single-author synthetic Python RSA pilot and raw errors |
| D10 | Pass | Offline-schema-validated SARIF 2.1.0 and CycloneDX 1.7 CBOM |
| D11 | Pass, fail-closed | All 243 patch-gate states; no transformation approved |

## 1. Fresh-machine setup in WSL

Required tools:

- Git
- Python 3.10 or newer
- Java 21 and Maven
- Node.js 20 and npm

```bash
cd /home/ratneshp0411
git clone https://github.com/Ratneshp1122/PQMigrate.git pqc_migration_tool
python3 -m venv venv
source venv/bin/activate
pip install -r pqc_migration_tool/requirements-dev.txt
cd pqc_migration_tool/frontend
npm ci
```

Maven downloads its declared dependencies during the first test run. After Python, Maven, and npm dependencies are present, the validation uses vendored export schemas and does not need to upload source code.

## 2. One-command validation

```bash
cd /home/ratneshp0411/pqc_migration_tool
scripts/validate_d0_d11.sh
echo $?
```

Expected default exit code: `0`. The final line must be:

```text
Default result: PASS (exit 0).
```

To require every declared milestone to pass, run:

```bash
scripts/validate_d0_d11.sh --strict
echo $?
```

Expected strict exit code: `0`. A failed test, missing dependency, build failure, or missing evidence file returns `1`.

Other failure meanings:

- `1`: a test, build, schema validation, audit assertion, dependency check, or required evidence check failed.
- `64`: invalid command-line option.

## 3. What the command runs

1. Verifies Python dependencies and the Git/Java/Maven/Node/npm tools.
2. Confirms all required D0–D11 evidence documents exist and are non-empty.
3. Reruns the D0 registry classification against the current commit without overwriting the historical baseline.
4. Runs all 57 pytest tests, including ten focused D4 Go semantic cases.
5. Runs the legacy scanner’s 23 checks.
6. Runs PQMigrateBench v0.1 and verifies 72 raw predictions, split metrics, and visible errors.
7. Evaluates every one of the D11 gate’s 243 three-valued assignments.
8. Runs five Spring/Maven tests.
9. Builds the React frontend for production.
10. Scans the three controlled review fixtures and expects policy exit code `1` because vulnerable cryptography was found.
11. Checks schema 2.2, rules version, source commit, role coverage, five-stage traces, unknown exposure, and advisory-only plans.
12. Converts the same report to SARIF and CBOM and validates both against pinned official schemas.
13. Loads and lists all D7 rules.
14. Writes a machine-readable milestone matrix and captures runtime metadata.

## 4. Expected headline results

The exact timestamps, scan ID, and commit-derived trace IDs change between committed runs. The expected stable assertions are:

```text
57 passed
Results: 23/23 passed
Benchmark: pqmigratebench-0.1.0 (72 selected cases)
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
Validated SARIF 2.1.0 and CycloneDX 1.7 CBOM review artifacts.
Validated the D11 five-condition fail-closed patch gate across all 243 assignments.
```

The frontend currently emits a non-fatal warning because the main JavaScript chunk exceeds 500 kB. A warning is not a failed build, but it must remain in the limitation record.

## 5. Generated evidence

Inspect these after the command finishes:

| Artifact | Check |
|---|---|
| `review-artifacts/latest/d0-d11-validation-summary.json` | Overall status, per-day status, source commit |
| `review-artifacts/latest/d0-current-registry-audit.json` | Current registry classification |
| `review-artifacts/latest/three-fixture-report.json` | Canonical schema 2.2 report |
| `review-artifacts/latest/three-fixture.sarif.json` | SARIF 2.1.0 evidence |
| `review-artifacts/latest/three-fixture.cdx.json` | CycloneDX 1.7 CBOM evidence |
| `review-artifacts/latest/d9-benchmark-results.json` | Raw benchmark predictions and metrics |
| `review-artifacts/latest/d11-patch-policy-audit.json` | 243-state gate audit |
| `review-artifacts/latest/baseline-metadata.log` | Commit and runtime versions |
| `review-artifacts/latest/d0-d11-validation.log` | Complete top-level run log |

Quick manual inspection:

```bash
python3 -m json.tool review-artifacts/latest/d0-d11-validation-summary.json
python3 -m json.tool review-artifacts/latest/d11-patch-policy-audit.json
git status --short --branch
git rev-parse HEAD
```

Generated JSON evidence is refreshed by validation and may make the worktree dirty until the evidence is committed. Runtime `.log` files are intentionally not versioned.

## 6. Individual checks for debugging

```bash
cd /home/ratneshp0411/pqc_migration_tool

# D0
../venv/bin/python3 tests/d0_registry_audit.py \
  --commit "$(git rev-parse HEAD)" \
  --output /tmp/d0-current-registry-audit.json

# D2–D8, D10, D11 unit/integration contracts
cd /home/ratneshp0411
venv/bin/python3 -m pytest -q pqc_migration_tool/tests

# D7 rules
cd /home/ratneshp0411/pqc_migration_tool
../venv/bin/python3 cli.py list-rules

# D9 benchmark
scripts/run_benchmark.sh

# D10 direct exports; exit 1 from scan is expected when findings exist
set +e
../venv/bin/python3 cli.py scan tests/fixtures/review --format sarif --output /tmp/review.sarif.json
test "$?" -eq 1
set -e
../venv/bin/python3 cli.py export review-artifacts/latest/three-fixture-report.json \
  --format cbom --output /tmp/review.cdx.json

# D11 mathematical audit
cd /home/ratneshp0411
venv/bin/python3 -m pqc_migration_tool.patcher.policy_audit

# Backend and frontend
cd /home/ratneshp0411/pqc_migration_tool/backend && mvn test
cd /home/ratneshp0411/pqc_migration_tool/frontend && npm run build
```

## 7. Claims you may make after a successful run

- The bounded Python and Go paths distinguish controlled signature, key-transport, and unresolved-import cases.
- Decisions are rule-versioned, evidence-linked, and advisory-only.
- The D9 measurements reproduce on the committed single-author synthetic Python RSA pilot.
- SARIF and CBOM documents conform to the pinned schemas locally.
- Unknown patch conditions fail closed and current reports cannot authorize mutation.

Do not claim:

- general interprocedural or cross-file Go semantic resolution;
- product-wide or publication-quality accuracy;
- safe automatic migration;
- downstream-platform SARIF/CBOM import success;
- proven TLS/SSH/JWT interoperability;
- that passing tests proves deployment security.

The D4 evidence and its remaining boundaries are documented in `docs/review/d4-go-semantic.md`.
