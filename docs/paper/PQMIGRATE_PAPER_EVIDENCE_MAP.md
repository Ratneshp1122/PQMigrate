# First-paper evidence and editorial record

Date: 4 October 2026. Main manuscript: `PQMIGRATE_RESEARCH_PAPER_IEEE.md`.

## Delivered files

- `PQMIGRATE_RESEARCH_PAPER_IEEE.pdf`: seven-page, two-column IEEE-style review copy, rendered with ReportLab and visually reviewed on all pages.
- `PQMIGRATE_RESEARCH_PAPER_IEEE.tex`: standalone IEEEtran conference source with numbered sections, equations, tables, and bibliography. The Codex compiler returned `Unable to find standard directories for platform`; compilation of this LaTeX source is unverified. The delivered PDF was generated separately and is not represented as an IEEE-validated submission PDF.
- `PQMIGRATE_RESEARCH_PAPER_IEEE.md`: full editable editorial source, replacing the earlier scaffold as the current manuscript.
- `build_manuscript.py`: regenerates the standalone LaTeX source from Markdown.
- `build_review_pdf.py`: regenerates the visually reviewed PDF layout from Markdown; requires ReportLab, pypdf, and the specified Windows fonts. Inspect pagination after edits, especially the final reference-column break.

## Evidence identity

Implementation commit: `bcfb5e40fbc8eb74e1c919114f54031d03ab44e9`.

Dataset: `benchmarks/pqmigratebench_v0_1.jsonl`.

Dataset SHA-256: `293fee315c4fbcb95f0d071615ce54a7ac6c9b8b89783a832832c15e3697603b`.

Preserved run used for numerical checks:

```text
/home/ratneshp0411/pqmigrate-release-evidence/bcfb5e4/run2/artifacts/
```

Both full-run logs and checksum lists remain in sibling `run1/` and `run2/` directories. The source checkout is separate from this evidence. No new scanner experiment was performed while drafting; tables were checked against the preserved completed runs.

| Manuscript claim | Primary local evidence | Qualification |
|---|---|---|
| 72 total, 68 scored, 52 operations, 16 negatives, 4 malformed | `d9-benchmark-results.json`, category counts and metrics | Single-author synthetic Python RSA pilot |
| Full TP=40, FP=0, FN=12, TN=16 | `d18-baselines.json`, `systems.full_pipeline.metrics` | Snippet-level operation presence |
| Full F1=0.869565; role accuracy 40/40; coverage 40/52 | Same artifact, operation and role fields | Gold-operation-conditioned role measure |
| AST F1=0.88; roles 32/44 | Same artifact, `systems.ast_call_only.metrics` | Baseline does not resolve receiver identity |
| Five configurations in Tables III and IV | Same artifact, all `systems` entries | Two are post-prediction masks |
| Exact accuracy 56/68 | Same artifact, `additional_metrics.exact_operation_role_accuracy` | Includes 16 correctly rejected negatives |
| All 12 full-resolver mismatches are unsupported cases | `d9-benchmark-results.json`, `errors` | Not independently adjudicated root causes |
| Synthetic train/dev/test results | Same artifact, `split_counts` and `metrics_by_split` | Not repository holdouts |
| 97 Python tests | `python-pytest.log` | Engineering checks, not research sample size |
| 23 scanner and 5 Maven tests, frontend build | `day5-scanner-checks.log`, `backend-maven-test.log`, `frontend-build.log` | Local integration evidence |
| D0-D20 pass and deployment state | `d20-integration-summary.json` | No production deployment/security certification |
| Preview and temporary-copy checks | `d12-preview.json`, `d13-verification.json` | Bounded digest expression, not PQC migration |
| Two-party compatibility tests | `d14-interoperability.json` | Digest contract, not ML-KEM/ML-DSA |

## Corrections made during paper preparation

1. The lexical baseline is a substring lookup, not actual resolved-import analysis.
2. The two configurations called ablations in D18 are output masks; no internal stage is disabled and rerun.
3. Python role inference sorts scope nodes, so the paper uses an O(N log N) per-invocation bound under stated assumptions rather than asserting unconditional linear traversal.
4. The pilot couples operation presence to a known role and scores one result per snippet.
5. Conflicting roles are aggregated across a snippet; the implementation is not a complete per-call or sound binding analysis.
6. Random-source tracking is an implemented key-transport proxy, not proof that random bytes serve as a session key.
7. Role accuracy among answered gold operations is not the false-recommendation rate, and operation non-answer rate is not measured planner abstention.
8. Four malformed cases are separately accounted, not silently included in the 68-case accuracy denominator.
9. The full resolver does not outperform AST matching on operation F1; both results are reported.
10. The larger study, bootstrap intervals, independent annotation, Semgrep comparison, and PQC provider integrations are future work.

## Remaining editorial inputs

- Confirm each author's exact name, agreed order, affiliation, and corresponding email. The supplied order is Deepak Uplaonkar, Ratnesh Patnaik, Saravanan Kumar, Vaibhavi Shah, Prince Ostwal. Honorifics are omitted in the research-paper author line.
- Finalize an accurate contribution statement with the authors; none is invented in the manuscript.
- Select a target venue and its page limit/template. IEEE conference style is used as a concrete draft format; there is no universal Oxford or MIT paper template.
- Confirm any venue-specific disclosure or acknowledgments before submission; no funding, approval, conflict-of-interest, or contribution declaration has been invented.
- Faculty/security review, dependency triage, and release tagging remain separate release actions.

The eight-state superposition investigation is explicitly outside the paper's contributions and results.
