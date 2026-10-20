# Validation and interpretation

Environment: Windows x86-64, Python 3.12.14, Semgrep CE 1.181.0. Exact resolved
dependencies: `requirements-windows-py312.lock`; per-run system and file hashes:
`results/*/run.json`. Direct pins support a separate environment on other OSes.
The Windows engine requires a local socketpair, blocked by this execution
sandbox, so actual fixture/corpus scans ran outside that sandbox with approval.
No target dependencies were installed and no target code was run.

Engineering validation on 21 October 2026:

* Six harness tests passed: rejection of labels/duplicate IDs/traversal;
  source-integrity rejection before scanning; partial findings and duplicate-span
  retention; actual process timeout/crash/spawn failure and exact output bytes;
  version failure with complete unstarted-case accounting and overwrite refusal;
  SOP vocabulary/uncertainty invariants.
* Semgrep rule test runner: **8/8 passed**, across Python and Go engineering
  fixtures including aliased imports, grouped Go imports, qualified APIs,
  unresolved receivers and declarations/strings that must not match.
* Initial Go import-pattern parse failures were corrected using these fixtures
  before any corpus scan. No rule changes used annotation or corpus outcomes.
* All committed rule files compile in the pinned engine. Fixture coverage is not
  a guarantee of soundness or complete API coverage.

The versioned manifests contain all 72 pilot snippets (including the four inputs
designated malformed by the historical corpus) and all 119 pinned real-code
files. Semgrep's parser can accept an input that another Python parser rejects;
engine-complete status means no reported engine failure, not language validity or
correctness. Every raw diagnostic remains available. No annotator submission was
opened, no native finding was aligned to gold, and no accuracy was calculated.

Raw outputs are stored losslessly in `results/*.zip`. Each archive contains the
manifest, version stdout/stderr, run/summary JSON, complete ledger and all per-case
records/native stdout/stderr. It excludes copied upstream input files and local
settings. `ARCHIVE-SHA256.json` checks every preserved file. Extract to a fresh
directory; do not overwrite an existing run. The archive script verifies its ZIP
and every member hash. Committed `.gitattributes` prevents line-ending conversion
of the frozen rules, manifests, records and raw archives.

```text
python experiments/semgrep_baseline/archive_run.py experiments/semgrep_baseline/results/NEW_RUN
python -m zipfile -e experiments/semgrep_baseline/results/2026-10-21-pilot.zip NEW_EXTRACTION
```

Only operational execution/finding counts appear in the summaries. They are not
operation counts or performance rates and must not be compared with the paper's
historical snippet scores. Gold lock, exact operation-unit adjudication and the
separate ordinary-source search evaluation remain prerequisites for scoring.

Recorded executions: 72/72 pilot inputs and 119/119 real-code files have
engine-complete status; they produce 98 and 378 native rule findings respectively.
These are unscored engineering counts, including overlaps and uncertain candidates.
The actual engine reported no parse errors, timeouts or crashes in these runs;
failure paths are exercised in the harness tests, not fabricated in study output.
