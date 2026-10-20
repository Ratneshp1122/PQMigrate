# PQMigrate: Evidence-Driven and Abstention-Aware Planning for Post-Quantum Cryptographic Migration

> Revised 21 October 2026. The completed study is a single-author synthetic pilot. Real-code evaluation is ongoing. The supplied Draft 3 manuscript is revised separately under `revision/`; all historical result tables are unchanged.

## Abstract

Migrating software to post-quantum cryptography requires more than locating cryptographic names: the same primitive may implement signatures, general encryption, key transport, or protocol-specific behavior with different migration constraints. We present PQMigrate, a bounded static-analysis and planning system that links source evidence to operation roles, versioned migration knowledge, explicit blockers, and an abstention outcome when required context is unresolved. The current implementation analyzes Python and Go, emits traceable JSON, SARIF, and CycloneDX CBOM evidence, and enforces a fail-closed mutation policy. On a 72-case single-author synthetic Python RSA pilot, the full bounded pipeline achieved operation-detection precision 1.00, recall 0.769, and F1 0.870, while answering 40 of 52 gold operations with 1.00 role accuracy among answered cases. These preliminary figures are not product-wide accuracy results. Independent real-code annotation and external baseline comparison are ongoing and unscored. Our results motivate evaluating migration planners using both answer coverage and unsafe-recommendation rate rather than detection accuracy alone.

## 1. Introduction

ML-KEM and ML-DSA standardize different functions [1], [2]. A signature interface and key-transport interface therefore require different migration evidence. A KEM establishes shared secrets rather than replacing arbitrary-message encryption. Dependencies and coordinated change matter [3], [4]. Protocol identifiers [7] do not establish deployed support.

### Contributions

1. A typed, evidence-linked intermediate representation for cryptographic observations, operation roles and migration decisions.
2. Bounded Python and Go semantic inference that distinguishes confirmed operations from inventory leads and explicitly abstains on unsupported or conflicting evidence.
3. A versioned migration knowledge base and deterministic decision trace with blocker-aware, fail-closed patch eligibility.
4. A reproducible evaluation framework with same-corpus baselines, feature ablations, raw failure accounting and standards-based exports.

## 2. Research questions

- RQ1: How accurately does bounded semantic analysis distinguish operations from inventory-only evidence?
- RQ2: How accurately does it resolve migration-relevant roles?
- RQ3: What is the contribution of identity flow, session-secret evidence and protocol context?
- RQ4: How does abstention trade coverage for fewer unsafe recommendations?
- RQ5: Are decisions traceable and reproducible at an exact source commit?

## 3. Related work

**Discovery and migration dependencies.** Cryptoscope describes compiler-based analysis using control and data flow to identify cryptographic usage [9]. Hasan et al. model security dependencies and present migration case studies [4]. These works motivate connecting inventory entries to use and dependencies. PQMigrate's bounded heuristics are not equivalent to whole-program compiler analysis, and this pilot provides no shared-corpus comparison or performance ranking against these systems.

**Cryptographic API correctness.** CogniCrypt combines assistance for generating cryptographic code with checking its integration [10]. CrySL specifies correct API usage and supports context- and flow-sensitive checking [11]. CryptoGuard uses program-slicing refinements for detecting cryptographic vulnerabilities in Java projects [12]. CryptoAPI-Bench supplies Java API-misuse cases [13]. These tasks concern usage constraints or weaknesses. PQMigrate instead attempts to identify migration-relevant operation roles and produce conditional advice. This distinction does not make it a misuse detector, and none of the cited Java results transfers to the Python/Go setting without measurement.

**Inventory tools and interchange.** CodeQL documents a Python query for broken or weak cryptographic algorithms [14]. The Sonar cryptography plugin and CBOMkit provide cryptographic discovery and CBOM tooling [15], [16]. CycloneDX CBOM represents cryptographic assets and relationships [17]; SARIF standardizes static-analysis result interchange [18]. An export can satisfy a schema while containing an incorrect source interpretation. Structural validation is therefore separate from detection accuracy, role correctness and downstream ingestion. These tools are relevant comparators or integration targets, not baselines already evaluated in this manuscript.

**Reject options and reporting.** Chow studies the error/reject trade-off [20]; selective-classification research formalizes coverage and error among accepted predictions [19], [21]. This motivates reporting answered-case correctness together with coverage. PQMigrate does not satisfy the assumptions of a learned selective classifier or inherit a statistical guarantee from those papers. In particular, absence of a resolved role differs from a planner's decision to abstain from advice. The completed pilot measures the former, not the latter.

**External rule-engine baseline.** Semgrep runs published source patterns through its analysis engine [26]. The separate baseline implementation pins engine version, rules, source hashes and execution limits. Custom rules define the evaluated detector; results cannot be generalized to all Semgrep rule sets or commercial capabilities. Its execution ledger is not an accuracy evaluation. Native spans must be aligned to locked operation units before comparison.

## 4. System design

### 4.1 Threat model and scope

PQMigrate treats scanned repositories as untrusted input and does not execute target source during analysis. Its bounded inference is not whole-program proof. Unknown identity, role, compatibility, tests or authorization causes abstention or patch refusal.

### 4.2 Evidence pipeline

Discovery yields source-linked leads; bounded inference attempts operation and role resolution; CryptoIR links evidence to the versioned knowledge base and conditional plans. SARIF and CBOM exports serialize this evidence [17], [18]. Schema validity does not establish semantic correctness or downstream ingestion. Selected name/assignment heuristics and the random-byte key-transport proxy are fallible [24].

### 4.3 Abstention and patch policy

Patch eligibility requires known role, supported construction, interoperability evidence, adequate tests and explicit operator authorization. Any false or unknown condition refuses mutation. The current paper evaluates planning and preview evidence; it does not claim automatic PQC transformation.

## 5. Dataset and annotation methodology

The completed study uses 72 single-author synthetic Python RSA snippets: 52 operations, 16 negative controls and four malformed inputs. Historical detection/role scores use 68 parseable snippets. Unsupported valid operations remain in the denominator. The pilot is not independent repository validation.

The 19-23 October 2026 annotation window is an organizational schedule, not evidence of completion. Reviewer eligibility requires not having built the scanner/resolver or seen predictions for the target repositories. Both reviewers independently receive the same 500 anchors, not disjoint halves. No A/B submissions were inspected for this revision or the baseline work. Reviewer interaction about individual cases remains prohibited until both packets are submitted and locked.

A separate unscored calibration batch of approximately 25 anchors must precede production work. It is not the production packet's first 25 rows. The organizer freezes an agreed feasible list of production candidate IDs before review; unassigned rows remain unreviewed and cannot be selected afterward based on favorable labels. Each reviewer works on a private copy with identifying columns and row order preserved.



At each pinned repository commit, reviewers inspect the whole containing function and follow imports, declarations, assignments, wrappers and callers as needed. The hash refers to the entire source file. Source is read and searched; target builds, installers and code are not executed. A proven source-level crypto call or wrapper is an operation even in tests; an import or familiar method name alone is not.

The SOP labels presence as yes/no/uncertain. Operation values are sign, verify, encrypt, decrypt, key_establish, hash, mac, kdf, key_generate, other_crypto, none and uncertain. Role values are signature, key_transport, key_establishment, encryption, hash, mac, kdf, key_management, other, none and uncertain. Unknown receivers or opaque boundaries require an uncertainty reason, rather than a guessed crypto identity. A non-crypto call uses no/none/none. Key creation maps to key_generate/key_management. Application evidence is required for key transport; encrypting random bytes alone is insufficient.

For multiple distinct operations at an anchor, presence is yes, operation and role are uncertain, and a MULTIPLE note identifies exact spans for adjudicator expansion. A wrong-line anchor is needs_context rather than silently relocated. Every completed row needs context and decisive source evidence. Operational definitions for setup calls, streaming stages and one-to-many alignments must be frozen before scored mapping; unresolved questions have been flagged to Ratnesh in repository issue 1 [24]. His instruction is to use the SOP taxonomy.

The study lead receives and locks both original files privately before comparing them. Preserve original disagreements and rationales, then adjudicate; do not replace original labels when computing agreement. Report raw agreement and Cohen's kappa [25] per applicable nominal field with prevalence, completed-pair counts, missing/unreviewed rows and any undefined denominator. No agreement has yet been measured. Calibration, assigned production rows and adjudicated expansions must be traceable as different stages.

After the first wave, the separate 240-anchor independent-search/ordinary-source packet is intended to investigate missed operations. Its design, frozen units, discovery effort and review coverage must be documented before estimating recall or TPR. The candidate-selected packet alone cannot support these claims. Repository families and near duplicates should remain in the same split; final sample sizes must be reported as observed rather than treated as achieved targets.

**Baseline and failure accounting.** The Semgrep comparison uses the same pinned Python/Go source revisions, published custom rules and the SOP vocabulary [26]. Preserve native findings and spans, raw stdout/stderr, exact versions, input/rule hashes, runtime limits and failure ledgers. Parse failures, timeouts, crashes, skipped files and unavailable sources must remain visible. A partial scan may contain findings and still be incomplete; neither a failure nor a no-match is automatically a gold negative. Duplicate/nested findings require a prespecified alignment policy, not favorable post hoc matching.

Do not tune rules from A/B submissions. Gold must be locked before accuracy calculations, and reporting must include unfavorable results and missingness. The current revision contains no Semgrep accuracy estimate, no real-code precision/recall/TPR, and no inter-annotator agreement. Future table changes require an auditable, comparable experiment and a transparent version note rather than a rule that only better outcomes are published.

## 6. Baselines and ablations

- Primitive/import lookup.
- Regex call matching.
- AST method matching.
- Full PQMigrate.
- Pinned Semgrep Community Edition with published rules.
- No-session-secret-flow and no-protocol-context ablations.

The future scored comparison requires identical locked cases, gold definitions, denominators and explicit failure policies. Semgrep is currently an unscored external-engine baseline with custom rules [26]. Historical output masks are not independently implemented feature-removal ablations.

## 7. Preliminary pilot results

| System | Operation F1 | End-to-end role accuracy | Error count |
|---|---:|---:|---:|
| Primitive lookup | 0.741 | 0.000 | 68 |
| AST method only | 0.880 | 0.615 | 24 |
| No session-secret flow | 0.870 | 0.538 | 24 |
| No protocol context | 0.870 | 0.769 | 20 |
| Full pipeline | 0.870 | 0.769 | 12 |

These results use the 72-case single-author synthetic Python RSA pilot. The AST-only baseline has higher operation F1 than the full pipeline, illustrating why detection F1 alone does not measure role correctness or safety. No real-code accuracy, TPR, agreement or new confidence intervals are available. Historical numbers must not be replaced merely because a new outcome is better.

## 8. Error analysis

The supplied manuscript records a PS256 JWT non-coverage probe and two random-value encryptions incorrectly inferred as key transport. RFC 7518 confirms PS256 is an RSA-PSS algorithm [22]. These are supplementary diagnostic counterexamples, not an independent test-set estimate. Name tracking, scope boundaries and output aggregation require further evaluation [24].

## 9. Discussion

Report answered-case correctness with coverage; selective-prediction research motivates these separate quantities [19]-[21] but does not provide guarantees for this heuristic resolver. A role non-answer is distinct from planner abstention. Advice correctness and unsafe-recommendation rates remain unmeasured.

## 10. Threats to validity

The synthetic pilot diagnoses what the bounded resolver can and cannot express. It cannot support claims of superiority over external tools, real-code accuracy, reduced migration effort or safer recommendations. Better detection F1 can coexist with worse role assignment; conversely, selective non-answers can inflate correctness among answered cases while leaving useful operations unresolved. The historical table must be interpreted with both the task and denominator visible.

**Internal and construct validity.** A single author selected examples, defined labels and implemented the analyzer. Repeated scenario templates and a deliberately supported/unsupported mixture can favor the implementation. Snippet presence was historically coupled to a known role for some systems. Call-level operation presence, application role and planner advice are distinct constructs. Masking outputs is not a feature-removal experiment. Neither non-execution nor passing syntax/schema checks establishes semantic correctness. The random-byte key-transport proxy is specifically insufficient under the reviewer SOP.

**External validity.** The completed numerical evidence is Python/RSA-specific and synthetic. It does not establish Go performance, wrapper resolution, package-boundary behavior, protocol coverage or operational deployment characteristics. The 500 candidate-selected anchors focus on scanner-discoverable locations; even complete annotation of them cannot reveal all missed operations. The separate ordinary-source/independent-search packet is needed to study omissions. Whole-file Semgrep scans provide more context than isolated snippets but do not solve sampling bias or establish whole-repository coverage.

**Statistical validity.** Correlated examples, author selection and few repository families limit inference. No significance test, real-code confidence interval or inter-annotator agreement result is available. Once units and gold are locked, report raw denominators, label prevalence, undefined metrics and repository dependence alongside any interval. A planned repository bootstrap is not automatically reliable with few independent clusters; resampling must preserve paired systems and repository families. There is no statistical basis for selectively publishing only improvements over the historical table.

**Reproducibility and standards drift.** Pin the code, corpus, rule files, mapping, dependencies and standards access date. Mutable product documentation is evidence of documented capabilities at access time, not of a frozen tool's measured behavior. The inspected source and corpus are available at [24]; externally stored historical gate logs remain a verification gap. The IEEE-formatted bibliography identifies primary sources and versions; the accompanying audit distinguishes standards, author manuscripts, documentation, repository evidence and publisher metadata.

**Planning and security validity.** A resolved role is necessary evidence for some migration advice, not sufficient evidence of a correct redesign. KEM selection does not itself settle key confirmation, authentication, serialization, failure handling or protocol integration [1], [4]. ML-DSA identifiers in a protocol specification do not prove deployment readiness [7]. No cryptographic security proof, verified PQC transformation, production interoperability measurement or user study is contributed here. Separate proposed cryptography investigations contribute no result to this paper.

The current pilot is synthetic, single-author, Python/RSA-specific and correlated by scenario family. The implemented analysis is bounded and does not establish whole-program behavior. Standards-valid exports do not prove downstream ingestion, and digest-contract interoperability does not establish ML-KEM, ML-DSA, TLS or production compatibility.

## 11. Reproducibility

The historical manuscript reports two clean D0–D20 gate runs at `bcfb5e40fbc8eb74e1c919114f54031d03ab44e9` [24]. The source revision and corpus are inspectable, but the externally held full gate logs were not independently verified for this revision. See `revision/README.md`, `references.json` and `build-audit.json` for source, citation and unchanged-page verification. No target code was executed for annotation or manuscript source inspection.

## 12. Conclusion

The prototype and synthetic pilot expose evidence and reporting limits. Independent real-code annotation, external comparison and validated transformations remain ongoing; no generalization or migration-safety claim follows from the pilot.

## References

[1] National Institute of Standards and Technology, Module-Lattice-Based Key-Encapsulation Mechanism Standard, FIPS 203, Aug. 2024, doi: 10.6028/NIST.FIPS.203. [Online]. Available: https://csrc.nist.gov/pubs/fips/203/final

[2] National Institute of Standards and Technology, Module-Lattice-Based Digital Signature Standard, FIPS 204, Aug. 2024, doi: 10.6028/NIST.FIPS.204. [Online]. Available: https://csrc.nist.gov/pubs/fips/204/final

[3] D. Ott, C. Peikert, and other workshop participants, "Identifying Research Challenges in Post Quantum Cryptography Migration and Cryptographic Agility," Computing Community Consortium workshop report, arXiv:1909.07353, 2019, doi: 10.48550/arXiv.1909.07353. [Online]. Available: https://arxiv.org/abs/1909.07353

[4] K. F. Hasan et al., "A Framework for Migrating to Post-Quantum Cryptography: Security Dependency Analysis and Case Studies," IEEE Access, 2024, doi: 10.1109/ACCESS.2024.3360412; author version arXiv:2307.06520v2. [Online]. Available: https://arxiv.org/abs/2307.06520v2

[5] National Institute of Standards and Technology, Stateless Hash-Based Digital Signature Standard, FIPS 205, Aug. 2024, doi: 10.6028/NIST.FIPS.205. [Online]. Available: https://csrc.nist.gov/pubs/fips/205/final

[6] National Institute of Standards and Technology, "Post-Quantum Cryptography," project status. Accessed: Oct. 21, 2026. [Online]. Available: https://csrc.nist.gov/projects/post-quantum-cryptography

[7] M. Prorock and O. Steele, "ML-DSA for JSON Object Signing and Encryption (JOSE) and CBOR Object Signing and Encryption (COSE)," RFC 9964, May 2026, doi: 10.17487/RFC9964. [Online]. Available: https://www.rfc-editor.org/rfc/rfc9964.html

[8] NIST National Cybersecurity Center of Excellence, "Migration to Post-Quantum Cryptography." Accessed: Oct. 21, 2026. [Online]. Available: https://www.nccoe.nist.gov/applied-cryptography/migration-to-pqc

[9] M. Moffie et al., "Cryptoscope: Analyzing cryptographic usages in modern software," arXiv:2503.19531v1, Mar. 2025, doi: 10.48550/arXiv.2503.19531. [Online]. Available: https://arxiv.org/abs/2503.19531

[10] S. Krüger et al., "CogniCrypt: Supporting Developers in using Cryptography," author manuscript, 2017. [Online]. Available: https://www.eclipse.org/cognicrypt/resources/publications/knr%2B17cognicrypt.pdf

[11] S. Krüger, J. Späth, K. Ali, E. Bodden, and M. Mezini, "CrySL: An Extensible Approach to Validating the Correct Usage of Cryptographic APIs," in ECOOP, LIPIcs, vol. 109, 2018, pp. 10:1-10:27, doi: 10.4230/LIPIcs.ECOOP.2018.10. [Online]. Available: https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2018.10

[12] S. Rahaman et al., "CryptoGuard: High Precision Detection of Cryptographic Vulnerabilities in Massive-sized Java Projects," arXiv:1806.06881v5, 2019, doi: 10.48550/arXiv.1806.06881. [Online]. Available: https://arxiv.org/abs/1806.06881v5

[13] S. Afrose, S. Rahaman, and D. D. Yao, "CryptoAPI-Bench: A Comprehensive Benchmark on Java Cryptographic API Misuses," in Proc. IEEE SecDev, 2019, pp. 49-61; benchmark artifact. [Online]. Available: https://github.com/CryptoAPI-Bench/CryptoAPI-Bench

[14] GitHub, "Use of a broken or weak cryptographic algorithm," CodeQL Python query documentation. Accessed: Oct. 21, 2026. [Online]. Available: https://codeql.github.com/codeql-query-help/python/py-weak-cryptographic-algorithm/

[15] CBOMkit contributors, "Sonar Cryptography Plugin," source and documentation. Accessed: Oct. 21, 2026. [Online]. Available: https://github.com/cbomkit/sonar-cryptography

[16] CBOMkit contributors, "CBOMkit," source and documentation. Accessed: Oct. 21, 2026. [Online]. Available: https://github.com/cbomkit/cbomkit

[17] OWASP Foundation, "Cryptography Bill of Materials (CBOM)," CycloneDX documentation. Accessed: Oct. 21, 2026. [Online]. Available: https://cyclonedx.org/capabilities/cbom/

[18] OASIS, Static Analysis Results Interchange Format (SARIF) Version 2.1.0 Plus Errata 01, OASIS Standard, Aug. 2023. [Online]. Available: https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/sarif-v2.1.0-errata01-os-complete.html

[19] Y. Geifman and R. El-Yaniv, "Selective Classification for Deep Neural Networks," arXiv:1705.08500v2, 2017, doi: 10.48550/arXiv.1705.08500. [Online]. Available: https://arxiv.org/abs/1705.08500v2

[20] C. K. Chow, "On Optimum Recognition Error and Reject Tradeoff," IEEE Trans. Inf. Theory, vol. 16, no. 1, pp. 41-46, Jan. 1970, doi: 10.1109/TIT.1970.1054406. [Online]. Available: https://research.ibm.com/publications/on-optimum-recognition-error-and-reject-tradeoff

[21] R. El-Yaniv and Y. Wiener, "On the Foundations of Noise-free Selective Classification," J. Mach. Learn. Res., vol. 11, no. 53, pp. 1605-1641, 2010. [Online]. Available: https://www.jmlr.org/papers/v11/el-yaniv10a.html

[22] M. Jones, "JSON Web Algorithms (JWA)," RFC 7518, May 2015, doi: 10.17487/RFC7518. [Online]. Available: https://www.rfc-editor.org/rfc/rfc7518.html

[23] J. A. Hanley and A. Lippman-Hand, "If Nothing Goes Wrong, Is Everything All Right? Interpreting Zero Numerators," JAMA, vol. 249, no. 13, pp. 1743-1745, Apr. 1983, doi: 10.1001/jama.1983.03330370053031. [Online]. Available: https://jamanetwork.com/journals/jama/article-abstract/385438

[24] PQMigrate project, "PQMigrate source code and evaluation artifacts," Git repository, evaluated revision bcfb5e40fbc8eb74e1c919114f54031d03ab44e9, 2026. [Online]. Available: https://github.com/Ratneshp1122/PQMigrate/tree/bcfb5e40fbc8eb74e1c919114f54031d03ab44e9

[25] J. Cohen, "A Coefficient of Agreement for Nominal Scales," Educ. Psychol. Meas., vol. 20, no. 1, pp. 37-46, Apr. 1960, doi: 10.1177/001316446002000104. [Online]. Available: https://journals.sagepub.com/doi/abs/10.1177/001316446002000104

[26] Semgrep, "Run rules," documentation. Accessed: Oct. 21, 2026. [Online]. Available: https://docs.semgrep.dev/running-rules
