# PQMigrate real-code study runner

This study moves evaluation onto real Python and Go repositories while retaining the 72-case synthetic pilot as regression evidence. A repository scan establishes observed tool behavior; independent human labels are required before reporting precision, recall, role correctness, or advice safety.

## Frozen implementation and corpus

The runner requires an unchanged checkout of PQMigrate commit `bcfb5e40fbc8eb74e1c919114f54031d03ab44e9` in a directory named `pqc_migration_tool`. It scans jpadilla/pyjwt, paramiko/paramiko, pyca/cryptography, golang-jwt/jwt, go-jose/go-jose, and golang/crypto. These are purposive exploratory choices covering JWT, SSH, JOSE, and cryptographic libraries. They are not a random sample of software or unseen test repositories.

The first acquisition records each exact repository commit in `targets.lock.json`. Subsequent runs require those same revisions. Target package installation, imports, compilation, build scripts and tests are never invoked. License-file links and hashes are retained. Target tests and fixtures can be scanned and are distinguished from other source in a separate file ledger.

## Reproduce in WSL

The first completed run uses the existing `/home/ratneshp0411/venv/bin/python` environment; its exact Python and dependency versions are recorded in `protocol.json`. Dependencies are PyYAML, jsonschema, tree-sitter, and tree-sitter-go as required by the frozen project.

```bash
/home/ratneshp0411/venv/bin/python \
  /home/ratneshp0411/pqc_migration_tool/experiments/real_code_study.py \
  --source /home/ratneshp0411/pqmigrate-real-code-study/source/pqc_migration_tool \
  --workspace /home/ratneshp0411/pqmigrate-real-code-study \
  --output /home/ratneshp0411/pqc_migration_tool/review-artifacts/real-code/reproduction-01
```

Choose a new output directory for each run. Existing output directories are refused to preserve earlier evidence. A full source checkout is required; do not run target repositories' dependency installers. The isolated scanner checkout and downloaded repositories are outside the working project; result artifacts and the runner are in the project.

## Accounting and interpretation

Every attempted repository has an acquisition outcome. Each acquired repository has a scan timeout of 180 seconds. Exit 1 with a valid report is the CLI's expected findings-present outcome, not automatically a crash. Failures and timeouts remain in the summary. Commands, stdout/stderr, target and scanner commits, report checksums, wall time and file accounting are preserved. Timings include CLI startup and reporting and are descriptive, not a controlled performance benchmark.

The original scanner may omit parse errors from its JSON report. A separate worker applies Python AST / Go Tree-sitter parsing to eligible tracked files and records errors and exclusions. This ledger is external observation; it does not claim those diagnostics came from the CLI. Language-selection and file-exclusion policies also constrain what is scanned. Non-Python/Go code is outside this study's scope.

Finding counts are report records, not unique cryptographic operations or proven vulnerabilities. Known roles and planner decisions are predictions until reviewed. Multiple leads can repeat one inferred operation. A report containing zero findings cannot establish that the repository contains no cryptography.

## Review packet

For each successfully scanned repository, deterministic sampling selects up to 24 anchors from a separate text search, 8 from scanner findings, and 8 from ordinary source lines. This gives a target of 240 anchors. The text search is a discovery channel, not an executed scoring baseline. Ordinary-source selections are candidate controls, not assumed negatives. Snippets, exact locations, commit permalinks, source hashes and snippet hashes are retained. Duplicate snippet hashes are listed for review.

Two separate annotation files contain no model predictions. They are blank forms, not completed independent annotation. Reviewers must inspect whole functions and relevant callers, delimit operation units, record presence/role/operation/context and uncertainty, and avoid treating a short snippet as sufficient evidence when it is not. The adjudication process must preserve both original label sets and disagreement reasons. Advice correctness needs a separate label and defined decision scope.

All six exposed repositories must remain in exploration/development; related forks and duplicated code must be grouped before an additional held-out corpus is selected. Do not relabel these as a blind test after inspecting results or tuning the resolver. Keep synthetic regression results, exploratory repository observations, and independently adjudicated evaluation clearly identified in the manuscript.
