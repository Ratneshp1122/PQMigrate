# PQMigrate first-paper execution plan

**Working title:** *PQMigrate: Evidence-Driven and Abstention-Aware Planning for Post-Quantum Cryptographic Migration*  
**Target deliverable:** complete internal manuscript draft  
**Draft deadline:** 5 October 2026 (Asia/Calcutta)  
**Primary claim:** operation-aware evidence, context inference, and explicit abstention support safer and more traceable migration planning than primitive/API lookup alone.  
**Non-claim:** this paper does not claim automatic PQC transformation, production deployment, or completed ML-KEM/ML-DSA interoperability.

## 1. Verified engineering and artifact status

- [x] Commit `bcfb5e40fbc8eb74e1c919114f54031d03ab44e9` pushed to `origin/main`.
- [x] Clean detached checkout created from that exact commit.
- [x] D0–D20 gate passed from the clean checkout.
- [x] D0–D20 gate passed a second time after restoring the checkout.
- [x] Both complete logs and generated artifacts preserved outside the source tree.
- [x] Clean-checkout readiness confirms no missing files and no dirty paths.
- [ ] Faculty/security review recorded.
- [ ] `v0.1.0` annotated tag created after review.
- [ ] `v0.1.0` tag pushed.
- [ ] Frontend dependency audit reviewed: current clean install reports 2 moderate and 5 high vulnerabilities.

External release evidence is preserved at:

```text
/home/ratneshp0411/pqmigrate-release-evidence/bcfb5e4/
├── clean-readiness.json
├── run1/
│   ├── validation.log
│   ├── artifacts/
│   ├── post-run-status.txt
│   └── SHA256SUMS
└── run2/
    ├── validation.log
    ├── artifacts/
    ├── post-run-status.txt
    └── SHA256SUMS
```

Generated evidence is deliberately published outside the source commit. This prevents the act of regenerating timestamped evidence from changing the commit that the evidence validates. The release asset must state the source commit, toolchain versions, command, exit status and checksums.

## 2. Paper research questions

- **RQ1 — Operation detection:** How accurately does bounded semantic analysis distinguish real cryptographic operations from inventory-only evidence?
- **RQ2 — Role resolution:** How accurately does it distinguish signature, key transport, encryption, key establishment and unresolved use?
- **RQ3 — Evidence contribution:** What changes when identity flow, session-secret flow or protocol context is removed?
- **RQ4 — Abstention:** How does explicit abstention trade answer coverage for fewer unsafe recommendations?
- **RQ5 — Traceability:** Can a reviewer trace a recommendation or refusal from source evidence through a versioned rule and deterministic decision record?
- **RQ6 — Reproducibility:** Can the complete bounded pipeline and its exports be reproduced at an exact commit without modifying the user source?

## 3. Claims-to-evidence matrix

| Claim | Required evidence | Current state |
|---|---|---|
| Semantic evidence improves over primitive lookup | Same-corpus paired baselines and confidence intervals | Pilot exists; larger corpus required |
| Data flow improves role resolution | No-secret-flow ablation | D18 pilot complete |
| Protocol context adds useful evidence | No-context ablation | D18 pilot complete |
| Abstention reduces unsafe advice | Coverage versus false-recommendation analysis | Metric implementation required |
| Decisions are auditable | Finding, source span, rule/version, blockers and trace ID | Implemented |
| The tool is reproducible | Two clean runs at exact commit plus checksums | Complete for `bcfb5e4` |
| The tool performs automatic PQC migration | End-to-end ML-KEM/ML-DSA transformation evidence | Explicitly outside this paper |

## 4. Dataset target and sampling plan

### 4.1 Target size

Build **240 reviewed cases** as the primary target. Acceptable first-paper range is 200–300 after exclusions are documented.

Proposed composition:

| Category | Target |
|---|---:|
| Signature | 40 |
| Key transport | 36 |
| General asymmetric encryption/decryption | 36 |
| Key establishment and protocol-linked use | 28 |
| Negative controls/import-only/key-created-but-unused | 40 |
| Valid but unsupported flows | 32 |
| Conflicting or ambiguous roles | 16 |
| Parser failures or unsupported syntax | 12 |
| **Total** | **240** |

Language target:

```text
Python: 120 cases
Go:     120 cases
```

Do not force exact balance if the real repository pool cannot support it. Report actual denominators and sampling deviations.

### 4.2 Repository selection

- [ ] Select approximately 16 repositories: eight Python and eight Go.
- [ ] Record selection criteria before evaluating PQMigrate.
- [ ] Require a recognized open-source license.
- [ ] Pin repository URL and full commit SHA.
- [ ] Include different domains: web/security libraries, authentication, networking, infrastructure and general applications.
- [ ] Avoid selecting repositories only because PQMigrate performs well on them.
- [ ] Cap cases per repository so one project cannot dominate results.
- [ ] Preserve every exclusion and its reason.

Candidate discovery must combine multiple routes so PQMigrate cannot define its own gold corpus:

1. library import/API lookup;
2. independent regex search;
3. Semgrep candidate discovery;
4. PQMigrate candidate discovery;
5. random files from the selected repositories for negative controls.

Union all candidates, deduplicate by repository/commit/path/span, then perform stratified random sampling. Preserve the unsampled candidate ledger.

### 4.3 Repository-separated split

- [ ] Assign entire repositories—not individual snippets—to `train`, `dev` or `test`.
- [ ] Keep both languages represented in every split.
- [ ] Target approximately 60/20/20 by case count.
- [ ] Never tune rules against test repositories.
- [ ] Detect forks or copied/template code and keep related repositories in one split.
- [ ] Hash normalized snippets to detect duplicates across splits.
- [ ] Freeze `splits-v1.json` before evaluating the final system.

The split is for rule-development discipline; PQMigrate does not train a statistical model.

### 4.4 Annotation unit and schema

The annotation unit is one candidate cryptographic operation or one explicit negative-control location. Required fields:

```text
case_id
dataset_version
repository_url
repository_license
repository_commit
file_path
start_line / end_line
source_sha256
language
split
candidate_source
primitive_family
is_operation
operation
role
protocol_context
key_or_material_identity
secret_source
supported_by_current_scope
expected_planner_outcome
expected_rule_family
blocker_codes
parse_status
annotator_id
annotation_timestamp
rationale
```

Allowed primary role labels:

```text
signature
key_transport
encryption
key_establishment
hash
unknown
not_an_operation
```

Annotators must label observed behavior, not the migration they personally prefer. `unknown` is a valid gold label when the bounded code evidence does not establish one role.

### 4.5 Source preservation and licensing

- [ ] Store the smallest reviewable excerpt allowed by the repository license.
- [ ] Otherwise store commit, path, span and hash with a reproducible extraction script.
- [ ] Never silently edit real code into an easier case.
- [ ] Mark synthetic augmentation separately from real-repository cases.
- [ ] Preserve original whitespace and encoding metadata where possible.
- [ ] Remove secrets, credentials and personal data if discovered; record the exclusion without reproducing the sensitive value.

## 5. Independent annotation protocol

### 5.1 People and blinding

- [ ] Recruit two human annotators with programming and basic cryptography knowledge.
- [ ] Do not count the tool author and an AI-assisted copy of the author's labels as independent annotation.
- [ ] Hide PQMigrate and baseline predictions during independent annotation.
- [ ] Give both annotators the same frozen guide and repository context.

### 5.2 Calibration

1. Select 20 calibration cases that will not appear in the final test set.
2. Both annotators label independently.
3. Discuss ambiguous definitions, not individual desired outcomes.
4. Revise and version the annotation guide.
5. Restart final annotation with the frozen guide.

### 5.3 Final annotation and adjudication

- [ ] Annotator A labels all selected cases independently.
- [ ] Annotator B labels all selected cases independently.
- [ ] Preserve raw A and B labels unchanged.
- [ ] Generate field-by-field disagreement records.
- [ ] A third adjudicator or faculty reviewer resolves disagreements.
- [ ] Record the final label, adjudicator, rationale and resolution type.
- [ ] Do not delete disagreements after adjudication.

Recommended files:

```text
dataset/cases.jsonl
dataset/annotations/annotator-a.jsonl
dataset/annotations/annotator-b.jsonl
dataset/annotations/disagreements.jsonl
dataset/annotations/adjudicated-gold.jsonl
dataset/annotation-guide-v1.md
dataset/splits-v1.json
```

### 5.4 Agreement reporting

For a nominal field, report observed agreement and Cohen's kappa:

```text
kappa = (p_o - p_e) / (1 - p_e)
```

Calculate separately for:

- operation present versus absent;
- role among cases both annotators consider operations;
- operation type;
- protocol context;
- supported versus unsupported;
- recommend versus abstain gold outcome.

Also report raw agreement, label prevalence, confusion matrices and the number of cases eligible for each calculation. Do not report one pooled kappa across incompatible hierarchical fields. A low kappa must trigger guide review or be reported as task ambiguity; do not relabel merely to inflate agreement.

## 6. Baseline experiment design

### B0 — Primitive/import lookup

Input: import name, package path or primitive token.  
Capabilities: inventory candidate only.  
Mapping: predicts `is_operation=true` whenever its token rule fires; role and operation remain `unknown`. These unknown role predictions count as wrong for role evaluation and are not excluded.

### B1 — Regex call matching

Use pinned language-specific regexes for `.sign`, `.verify`, `.encrypt`, `.decrypt`, JWT calls and selected Go RSA APIs. Do not resolve AST structure, receiver identity, aliases or data flow. Version the complete rule file.

### B2 — AST method matching

Parse the language and identify call/method names, but disable receiver identity, key tracking, secret-source tracking and protocol-context inference. Parse failures remain in the denominator.

### B3 — Full PQMigrate pipeline

Enable bounded identity flow, local data flow, session-secret evidence, context inference, conflict detection, versioned rules, and abstention.

### B4 — External reproducible engine

Use **Semgrep Community Edition** with:

- a pinned release version and container/image digest or locked package hash;
- repository-local Python and Go crypto rules;
- metrics disabled;
- local execution without source upload;
- JSON output;
- the same timeout, source cases and result mapping as all other systems.

The Semgrep engine is external, but the crypto rule pack is authored for this study and must be published. Describe it as an external parsing/matching engine baseline, not an independently developed PQC migration system.

Cryptoscope is important related work because it constructs crypto-asset inventories using parsing, data/control-flow analysis and program slicing. Its paper reports real Java-project and CamBench evaluation. If no runnable public artifact is available, compare scope and published methodology narratively; do not fabricate same-corpus Cryptoscope numbers.

### 6.1 Common harness contract

Every system receives the same immutable case list and must emit:

```text
case_id
status: answered | abstained | parse_failure | timeout | crash
is_operation
role
operation
protocol_context
recommendation outcome, if supported
runtime_ms
error_code
```

Common controls:

- [ ] Same gold file and case order.
- [ ] Same repository commits and extracted spans.
- [ ] Same per-case timeout.
- [ ] Same process-level memory limit where supported.
- [ ] Same no-network rule after dependencies are installed.
- [ ] Same denominator; crashes, timeouts and parse failures are never silently dropped.
- [ ] Same hardware and runtime environment record.
- [ ] Same mapping from raw tool output to evaluation labels.
- [ ] Raw outputs preserved before normalization.

## 7. Statistical analysis plan

### 7.1 Primary metrics

Report counts and denominators before ratios.

```text
operation precision = TP / (TP + FP)
operation recall    = TP / (TP + FN)
operation F1        = harmonic mean of precision and recall
answer coverage     = answered gold operations / gold operations
conditional role accuracy = correct roles / answered gold operations
end-to-end role accuracy  = correct roles / all gold operations
abstention rate     = abstained cases / attempted cases
false-recommendation rate = incorrect recommendations / all recommendations
unsafe-advice rate = incorrect recommendations / all attempted cases
parser-failure rate = parser failures / attempted cases
```

Add protocol-context accuracy, exact operation-and-role accuracy, timeout rate, crash rate, median runtime and p95 runtime.

### 7.2 Confidence intervals

Use **10,000 repository-cluster bootstrap replicates** rather than resampling individual snippets. Cases from the same repository are correlated.

For each replicate:

1. resample repositories with replacement inside the evaluated split;
2. include all selected cases from each sampled repository;
3. recompute the metric;
4. use the 2.5th and 97.5th percentiles as the 95% interval.

For system comparisons, use the same resampled repositories for both systems and report the paired metric difference with its 95% interval. Record the random seed and bootstrap implementation version.

### 7.3 Required stratification

Report:

- overall results;
- Python and Go separately;
- signature, key transport, encryption and key establishment separately;
- negative controls;
- unsupported cases;
- ambiguous/conflicting cases;
- train, development and held-out test repositories separately;
- real versus synthetic cases separately, if synthetic cases remain.

Do not tune after reading held-out test errors. Corrections after test inspection require a new dataset/tool version and a clearly labelled subsequent evaluation.

### 7.4 Error taxonomy

Every incorrect or abstained gold operation receives one primary error code:

```text
missed_candidate
import_or_alias_resolution
receiver_identity
cross_function_flow
cross_file_flow
wrapper_or_framework_api
secret_source_resolution
protocol_context
conflicting_roles
unsupported_language_construct
parse_failure
timeout
baseline_mapping_error
annotation_ambiguity
other_with_rationale
```

Report counts, percentages and representative examples without exposing sensitive code.

### 7.5 Required tables and figures

- [ ] Dataset composition by repository, language, split and category.
- [ ] Inter-annotator agreement and disagreement table.
- [ ] Main same-corpus baseline table with 95% intervals.
- [ ] Ablation table with paired differences.
- [ ] Coverage versus false-recommendation/unsafe-advice curve.
- [ ] Per-category performance chart.
- [ ] Error taxonomy chart.
- [ ] Runtime distribution table or box plot.
- [ ] System architecture and evidence-flow figure.

## 8. Paper structure and writing checklist

### Abstract

- [ ] Problem in one sentence.
- [ ] Gap: inventories do not automatically establish operation role or safe migration advice.
- [ ] Method: bounded semantic evidence, versioned rules and abstention.
- [ ] Dataset and baseline scope stated exactly.
- [ ] Main results with denominators and uncertainty only after the larger evaluation exists.
- [ ] No automatic-migration claim.

### Introduction

- [ ] Motivate crypto inventory versus migration-planning gap.
- [ ] Explain why RSA signing, encryption and key transport cannot share one replacement.
- [ ] State research questions.
- [ ] List three or four concrete contributions.

### Related work

- [ ] Crypto inventories and CBOM.
- [ ] Cryptoscope and operation-aware crypto-asset discovery.
- [ ] Cryptographic API misuse analysis and CamBench.
- [ ] Static analysis, program slicing and taint/data-flow systems.
- [ ] PQC migration guidance and crypto agility.
- [ ] Explain precisely how PQMigrate differs: planning evidence, abstention, decision traces and patch gating.

### System design

- [ ] Threat model and trust boundaries.
- [ ] CryptoIR schema.
- [ ] Python and Go inference scope.
- [ ] Knowledge-base rules.
- [ ] Planner, blockers and abstention.
- [ ] Exports and dashboard.
- [ ] Preview/verification as bounded assurance, not automatic migration.

### Methodology

- [ ] Repository selection.
- [ ] Candidate generation and sampling.
- [ ] Annotation guide and independent labels.
- [ ] Adjudication and kappa.
- [ ] Repository-separated splits.
- [ ] Baseline definitions.
- [ ] Common failure accounting.
- [ ] Statistical plan and seed.

### Results

- [ ] Answer every RQ separately.
- [ ] Include denominators and intervals.
- [ ] Separate test-set results from development results.
- [ ] Do not hide abstentions, parser failures, timeouts or crashes.

### Discussion and threats to validity

- [ ] Synthetic-pilot history.
- [ ] Repository and language selection bias.
- [ ] Annotation subjectivity.
- [ ] Correlated cases within repositories.
- [ ] Bounded intra-function/local data flow.
- [ ] No approved PQC transformation.
- [ ] External baseline capability differences.
- [ ] Generalization beyond Python/Go and selected libraries.

### Reproducibility

- [ ] Release commit and tag.
- [ ] Dependency locks and runtime versions.
- [ ] Dataset and annotation versions.
- [ ] Commands for every table and figure.
- [ ] Raw predictions and failure logs.
- [ ] Artifact checksums.
- [ ] License and data-availability statement.

## 9. Tomorrow's draft definition of done

The manuscript due tomorrow is an **internal first draft**, not a submission-ready empirical paper.

- [ ] Title and scope frozen.
- [ ] Abstract contains no future results presented as completed.
- [ ] Introduction and contributions drafted.
- [ ] Related-work skeleton with verified references.
- [ ] System design drafted from D0–D20 documentation.
- [ ] Research questions included.
- [ ] Dataset/annotation protocol included as planned methodology.
- [ ] Existing 72-case pilot clearly labelled pilot evidence.
- [ ] D18 baseline table included as preliminary results.
- [ ] Larger 240-case results left as explicit placeholders.
- [ ] Threats to validity drafted.
- [ ] Release/reproducibility section points to `bcfb5e4` evidence.
- [ ] No ML-DSA/ML-KEM integration claimed in this first paper.
- [ ] Faculty questions highlighted in comments.

Suggested writing order:

1. Contributions and RQs.
2. System design.
3. Methodology.
4. Preliminary results.
5. Threats and limitations.
6. Related work.
7. Introduction.
8. Abstract last.

## 10. Second PQMigrate paper/draft boundary

The next PQMigrate study may add both:

1. a bounded RSA-signature interface integrated with a pinned ML-DSA provider; and
2. a bounded key-establishment fixture using standardized ML-KEM or an approved hybrid construction.

That future work requires separate provider/version selection, serialization contracts, peer compatibility, negative cases, build/runtime tests, rollback, interoperability matrices and reviewer approval. Do not retroactively describe the first paper as having completed these transformations.

## 11. Separate quantum-state research track

Keep the superposition-state study separate from the PQMigrate manuscript.

Current defensible status:

```text
research question + literature + proposed eight-state experiment
```

Not yet defensible:

```text
new public-key construction
security proof
everlasting-security claim
benefit when combined with ML-KEM
```

Side-paper preparation checklist:

- [ ] Specify the eight pure or mixed states mathematically.
- [ ] Specify priors, state-preparation process and measurement access.
- [ ] Define the adversary's exact state-identification or distinguishing objective.
- [ ] Evaluate 1, 2, 4 and 8 legitimate copies.
- [ ] Compare with the `1/8` blind-guess baseline where priors are uniform.
- [ ] Report uncertainty and noise assumptions.
- [ ] Separate simulation observations from proven security.
- [ ] Add ML-KEM only after stating the additional security property sought from the quantum component.
- [ ] Use a separate dataset, repository area, results section and claim table.

## 12. Immediate action list

### Must complete for the internal draft

- [ ] Assign paper section owners.
- [ ] Produce manuscript skeleton.
- [ ] Insert verified D18 pilot table.
- [ ] Insert D0–D20 architecture/evidence diagram.
- [ ] Write limitations before conclusions.
- [ ] Ask two prospective annotators for availability.
- [ ] Freeze repository-selection criteria and annotation guide v1.

### Must complete before empirical submission

- [ ] Build and independently annotate the 200–300-case corpus.
- [ ] Adjudicate and report agreement.
- [ ] Implement regex and Semgrep baselines.
- [ ] Implement repository-cluster bootstrap statistics.
- [ ] Run all systems with common failure accounting.
- [ ] Freeze test results.
- [ ] Complete error analysis.
- [ ] Obtain faculty/security review.
- [ ] Triage frontend dependency vulnerabilities.
- [ ] Create and push `v0.1.0` only after approval.

