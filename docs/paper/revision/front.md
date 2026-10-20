# PQMigrate: Evidence-Driven and Abstention-Aware Planning for Post-Quantum Cryptographic Migration

Dr. Deepak Uplaonkar, Ratnesh Patnaik, Saravanan Kumar, Vaibhavi Shah, and Prince Ostwal

**Abstract.** PQMigrate is a bounded source-analysis and advisory-planning prototype. Its completed quantitative study is a single-author synthetic pilot of 72 Python RSA snippets, not an independent real-code evaluation. The historical results describe an authored mixture of supported operations, unsupported operations, negative controls and malformed inputs. They establish neither generalization nor migration safety. This revision separates source-level operations from application roles, relates the implementation to cryptographic inventory and API-misuse analysis, and specifies an independent evaluation protocol. Real-code annotation and the external Semgrep comparison remain ongoing and unscored. Historical performance results are omitted; the evaluation status and protocol are reported instead. Planner recommendation correctness, Go accuracy, deployed interoperability and PQC transformations have not been evaluated by this pilot.

**Index terms:** post-quantum cryptography, cryptographic inventory, static analysis, role inference, selective prediction, reproducibility.

## I. Introduction

NIST FIPS 203 defines ML-KEM for key encapsulation; FIPS 204 defines ML-DSA for signatures [1], [2]. FIPS 205 defines the hash-based signature standard SLH-DSA [5]. These functions are distinct. Replacing an RSA signature interface and redesigning an RSA key-transport interface require different evidence about key formats, peers, message sizes and failure handling. A KEM establishes a shared secret and does not offer arbitrary-message encryption as a drop-in replacement [1]. Finding an algorithm name is consequently an inventory lead, not a complete migration decision.

Cryptographic-agility work treats dependency management and coordinated change as research problems [3], [4]. NIST's NCCoE migration project separates cryptographic discovery from interoperability work [8]. PQMigrate addresses part of the evidence-management problem: observations link to source locations, bounded inference attempts to resolve their use, and an advisory planner records conditions and blockers. It does not establish that suggested replacements will interoperate or be secure in the target application.

Standards and deployment status must be dated. At the verification date, 21 October 2026, NIST lists Falcon and HQC standardization as ongoing [6]. RFC 9964 specifies ML-DSA identifiers for JOSE and COSE [7]. This protocol specification is not evidence that a particular dependency, peer or deployment supports those identifiers. No JOSE/PQC integration or transformation is evaluated here.

## II. Contribution and evidence boundary

The contribution is an inspectable prototype, an evidence-linked representation of observations and conditional advice, and a reproducible evaluation design. Python and Go parsing support is an implementation capability; the completed numerical pilot evaluates only synthetic Python RSA snippets. A source-level invocation is not proof that a production execution reached it. Test files may contain real crypto invocations, while an import, comment or algorithm descriptor alone is not an operation.

The paper asks whether bounded evidence can distinguish inventory leads, operations and application roles, and how unresolved evidence should be reported. It does not answer whether the prototype is accurate across repositories or whether its advice reduces migration risk. The present manuscript reports the system design, evaluation methodology and limitations. Historical performance tables and numerical findings have been removed. No replacement accuracy estimates are available before independent gold labels and operation-unit definitions are locked.


## III. Related work

**Discovery and migration dependencies.** Cryptoscope describes compiler-based analysis using control and data flow to identify cryptographic usage [9]. Hasan et al. model security dependencies and present migration case studies [4]. These works motivate connecting inventory entries to use and dependencies. PQMigrate's bounded heuristics are not equivalent to whole-program compiler analysis, and this pilot provides no shared-corpus comparison or performance ranking against these systems.

**Cryptographic API correctness.** CogniCrypt combines assistance for generating cryptographic code with checking its integration [10]. CrySL specifies correct API usage and supports context- and flow-sensitive checking [11]. CryptoGuard uses program-slicing refinements for detecting cryptographic vulnerabilities in Java projects [12]. CryptoAPI-Bench supplies Java API-misuse cases [13]. These tasks concern usage constraints or weaknesses. PQMigrate instead attempts to identify migration-relevant operation roles and produce conditional advice. This distinction does not make it a misuse detector, and none of the cited Java results transfers to the Python/Go setting without measurement.

**Inventory tools and interchange.** CodeQL documents a Python query for broken or weak cryptographic algorithms [14]. The Sonar cryptography plugin and CBOMkit provide cryptographic discovery and CBOM tooling [15], [16]. CycloneDX CBOM represents cryptographic assets and relationships [17]; SARIF standardizes static-analysis result interchange [18]. An export can satisfy a schema while containing an incorrect source interpretation. Structural validation is therefore separate from detection accuracy, role correctness and downstream ingestion. These tools are relevant comparators or integration targets, not baselines already evaluated in this manuscript.

**Reject options and reporting.** Chow studies the error/reject trade-off [20]; selective-classification research formalizes coverage and error among accepted predictions [19], [21]. This motivates reporting answered-case correctness together with coverage. PQMigrate does not satisfy the assumptions of a learned selective classifier or inherit a statistical guarantee from those papers. In particular, absence of a resolved role differs from a planner's decision to abstain from advice. The completed pilot measures the former, not the latter.

**External rule-engine baseline.** Semgrep runs published source patterns through its analysis engine [26]. The separate baseline implementation pins engine version, rules, source hashes and execution limits. Custom rules define the evaluated detector; results cannot be generalized to all Semgrep rule sets or commercial capabilities. Its execution ledger is not an accuracy evaluation. Native spans must be aligned to locked operation units before comparison.

## IV. System model and inference

Discovery produces source-linked leads, inference attempts identity and role resolution, and the intermediate representation links findings to a versioned migration knowledge base. The planner exposes advice with conditions, evidence and blockers. JSON, SARIF and CBOM exports serialize observations; they are not additional evidence about the target's behavior [17], [18], [24]. Scanned source is treated as input rather than imported or executed.

For the inspected Python resolver, assignment collection tracks selected RSA key-generation calls and selected random-byte sources. A subsequent pass associates calls with tracked names in a bounded scope. This is name-based evidence, not a general points-to analysis. Imports, assignments, wrappers, mutation and branch conditions may invalidate the inferred association. A role assigned from such evidence remains a fallible inference [24].

An encryption of bytes from a tracked random source is a heuristic proxy used by the historical implementation for key transport. Randomness does not establish that those bytes are key material. The reviewer SOP instead requires evidence of their application use. This limitation requires application-level evidence before assigning key transport.

## V. Methodology and interpretation

**Synthetic pilot and current study.** PQMigrateBench v0.1 is a single-author synthetic pilot of 72 Python RSA snippets, covering operations, negative controls and malformed inputs. The same developer authored and labeled the examples. These deliberately constructed families are not a random sample of real software and cannot establish generalization [24]. Historical performance scores, result tables, plots and numerical findings are excluded from this manuscript.

The inspected implementation revision is bcfb5e40fbc8eb74e1c919114f54031d03ab44e9 [24]. Source and corpus identity are recorded in the reproducibility audit. Source inspection supports implementation statements, but externally held historical gate logs were not independently verified. No historical gate-run outcome is claimed here.

**Units and coupled outputs.** The pilot's scoring unit is a snippet, whereas the real-code protocol uses source-level invocation units. A key may be generated, loaded, used to sign and serialized in one function: those invocations must not silently become one scored call. Historic coupled presence/known-role outputs must be distinguished from operation detection independent of role. An unresolved receiver is not a proven negative. A valid but unsupported operation remains eligible for annotation and failure accounting.

**JWT and aggregation limits.** Source inspection shows a literal RS-prefixed algorithm check for recognized JWT encoding. RFC 7518 defines PS256 as an RSA-PSS algorithm [22], so an RS-only check does not cover all RSA JWT signatures. This is an implementation-coverage limitation, not a new measured performance estimate. Mixed roles, wrappers, cross-scope flow, aliasing, reassignment and dynamic behavior can defeat bounded inference. The implementation's ordering and aggregation choices are not a soundness proof [24].

**Output masks.** The session-secret and protocol variants in the pilot mask information in existing outputs. They demonstrate consequences for the reported fields; they are not independent implementations that disable analysis features. Such masks must not be presented as independently implemented feature-removal ablations. A causal claim about a separately implemented analyzer would require a new experiment.

**Mutation policy.** The inspected policy checks role, construction support, interoperability evidence, tests and operator authorization, refusing mutation when requirements are false or unknown [24]. That control-flow property does not establish correct recommendations or secure transformed code. Tests, schema validity, source preservation, peer compatibility and cryptographic correctness are different obligations. Planner advice and unsafe-recommendation rates require separate independently adjudicated outcomes; this pilot supplies none.

**Statistical scope.** Correctness among selected answered cases does not establish reliability for a target population. Reject-option literature motivates joint coverage/error reporting but supplies no bound for this authored sample [19]-[21]. Zero observed events would not establish zero underlying risk [23]. No real-code precision, recall, TPR, agreement or confidence interval is asserted here.

The study's next stage is independent source annotation. The following sections distinguish implementation and execution status from accuracy evidence, then specify limitations and the ongoing review protocol.
