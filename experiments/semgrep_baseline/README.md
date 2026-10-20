# Reproducible, unscored Semgrep baseline

This is a custom-rule baseline using Semgrep Community Edition 1.181.0, not a
benchmark of Semgrep's commercial products or a complete cryptographic inventory.
Rules were specified from API syntax and engineering fixtures, without annotator
submissions. Ratnesh requested the reviewer SOP taxonomy on 21 October 2026.
Open operation-unit questions are recorded in [issue 1](https://github.com/Ratneshp1122/PQMigrate/issues/1).

## Frozen inputs

* `manifests/synthetic-pilot.json`: the existing 72 synthetic Python RSA snippets,
  projected to source-only fields. Includes all four malformed snippets. This is
  the same pilot, not independent validation; it contains no Go samples.
* `manifests/real-code.json`: 119 whole Python/Go files at six full commit hashes,
  from the source-verification manifest accompanying the 500 candidate anchors.
  Each whole-file SHA-256 is pinned. This is candidate-containing file coverage,
  not 500 independently scored operations, a repository-complete scan, or the
  separate 240-anchor ordinary-source/independent-search sample. No anchor labels
  are needed or read. The production evidence directory was not available on the
  public repository when this baseline was prepared.

The manifest, runner, rules and mapping hashes are recorded per run. Do not add
annotation fields to these manifests: the runner rejects unexpected case fields.
The pilot manifest's `original_corpus_sha256` records the actual working-copy
JSONL bytes used for projection. The evaluated commit's canonical Git blob hash
is `293fee315c4fbcb95f0d071615ce54a7ac6c9b8b89783a832832c15e3697603b`;
Windows CRLF checkout changes the JSONL container hash but not its decoded source
strings. Each projected snippet has its own exact source digest.
Download only pinned raw source, verify its hash, and never import or execute it.
Individual upstream sources remain subject to their repository licenses; pinned
repository/path/commit identifiers are in the manifest. No target dependencies
are installed. Whole-file scanning deliberately retains surrounding context.

## Install and rerun

Use Python 3.12 in a fresh virtual environment. The exact resolved environment is
recorded in `requirements-windows-py312.lock`; use that lock on Windows/Python
3.12 for the recorded environment. On other platforms resolve the direct pins
and save a new environment record, since pywin32 is Windows-specific:

```text
python -m venv .venv-semgrep
# Windows: .venv-semgrep\Scripts\activate
# POSIX: source .venv-semgrep/bin/activate
python -m pip install -r experiments/semgrep_baseline/requirements.txt
python -m pytest experiments/semgrep_baseline/tests -q
semgrep --test --config experiments/semgrep_baseline/rules experiments/semgrep_baseline/fixtures
python experiments/semgrep_baseline/runner.py --manifest experiments/semgrep_baseline/manifests/synthetic-pilot.json --output experiments/semgrep_baseline/results/pilot-new
python experiments/semgrep_baseline/runner.py --manifest experiments/semgrep_baseline/manifests/real-code.json --output experiments/semgrep_baseline/results/real-code-new --download
```

`--semgrep` accepts an absolute executable path without activating a venv.
`--source-root` accepts a verified cache arranged as
`OWNER__REPO/FULL_COMMIT/path`. Use a new output directory on each run: existing
directories are refused. Internet access is only necessary for installation and
missing source acquisition; scans disable metrics and version checks.

Rules are committed in JSON-compatible YAML; regenerate deterministically with
`python experiments/semgrep_baseline/build_rules.py`. Rule repairs may use only
engineering fixtures before the test corpus and gold labels are locked. Changes
to frozen rules require a new baseline version and a separate run, never silent
replacement of raw outputs.

## Execution contract

Every manifest input appears in the ledger, even if source acquisition, parsing,
scanning or mapping fails. A version failure records every unstarted case in the
summary. One scanner process handles one whole file with one Semgrep worker,
30 seconds per rule/file, a 120-second process-tree deadline, a 512 MB Semgrep
memory limit, and a 5 MB source limit. Two independent files run concurrently.
These are engine limits, not a container-enforced security boundary.

Each local run retains source bytes, exact stdout/stderr bytes, their digests, command,
return code, elapsed time, native errors and independent failure flags. Findings
from partial scans are retained with incomplete status; malformed JSON, parser
errors, skipped targets, crashes, engine errors and timeouts never become clean
negative observations. Raw files are not postprocessed. Summaries contain only
execution and finding counts, with `accuracy: null`. Process startup and rule
compilation are included in per-case elapsed time; runtime is not warmed-engine
throughput. A harness failure is also a ledger entry. Nonzero exit denotes an
incomplete run, not automatically no findings.

Raw stdout/stderr and records are committed unchanged. Copied target source files
(`raw/*/input.py` and `input.go`) and local Semgrep settings are excluded from Git;
recover source using the pinned manifest and hash checks. This avoids republishing
upstream source trees. Source-cache paths are never annotation inputs.

No accuracy or superiority claim is supported before independent gold is locked,
units are aligned, and denominators are preregistered. Never select publication
results only because they exceed the historical pilot. Preserve unfavorable and
failed results alongside favorable results.

See [OUTPUT_MAPPING.md](OUTPUT_MAPPING.md) for the SOP field contract.

See [VALIDATION.md](VALIDATION.md) for engineering checks and the lossless raw-run
archives. The recorded runs use four concurrent file workers; the rerun default
is two. `run.json` records the actual limits, so timing comparisons must account
for this difference. No scan uses annotator labels.
