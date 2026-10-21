# APPENDIX A PROPOSED MULTI ENGINE INTEGRATION

This proposed extension supplements Section XI without changing the completed pilot, its result tables, or the existing theory. It is a research and engineering plan; the four-engine platform has not been implemented or evaluated. The current quantitative study remains a single-author synthetic Python RSA pilot. Independent real-code labels and comparable accuracy measurements remain pending.

## A. Complementary evidence sources

We propose adapters for CryptoScan, Semgrep Community Edition, Where's Crypto?, and CRYLOGGER. CryptoScan would supply broad inventory candidates; Semgrep would supply findings from a frozen, independently specified source-rule set [A1], [A2]. These findings would enter PQMigrate as evidence to inspect rather than established application roles. The existing unscored Semgrep runner is a starting point, not evidence that four integrations are complete [A7].

Where's Crypto? studies primitive classification in binaries and provides an IDA proof of concept [A3]. A binary adapter would retain artifact hashes, function addresses, analysis configuration and unresolved source correspondence. CRYLOGGER records cryptographic API behavior in an instrumented Android environment [A4]. Its integration would require a separate Android/Java evaluation track; the tool is not a ready-made Python/Go runtime tracer. A runtime observation can establish that an instrumented call occurred in that test session, while non-observation cannot establish the absence of cryptography.

## B. Evidence correlation and planned operation

Each adapter would preserve native results, versions, configuration, hashes, limits and failure status. Source spans, binary addresses and runtime events would retain distinct identities. Correlation would require build or symbol evidence, with uncertain links left unresolved. Several tools reporting the same location would not count as independent confirmation, and findings would not be added together as unique operations.

The proposed platform would offer an inventory view, a source/binary/runtime evidence panel, a review queue, and a versioned migration-plan export. Role inference would use the reviewer SOP taxonomy, including uncertainty and distinct key-management operations. An encrypt call would indicate key transport only when application evidence supports that use. Missing receiver, role, construction or peer-compatibility evidence would continue to block automatic transformation. This platform design is a hypothesis about a useful review workflow, not a demonstrated safety advantage.

## C. Feasibility and deployment constraints

The initial delivery should prioritize the two source adapters and an inspectable evidence contract. Binary and runtime workers would be separate, optional components with their own dependencies and approved test environments. Existing proof-of-concept dependencies require compatibility assessment before any production claim. Runtime execution would be limited to explicitly authorized test workloads; raw sensitive parameters would require minimization and controlled retention.

Licensing must be checked for the exact releases, dependencies and distribution model. CryptoScan and CRYLOGGER publish Apache-2.0 and MIT licenses respectively; Semgrep engine and vendor-rule terms are separate. Restricted vendor rules must not be assumed reusable in a competing service. An explicit implementation license and IDA dependency rights have not been established for the inspected Where's Crypto? repository; that is a release gate, not a solved integration [A5], [A8]-[A11]. Repository popularity does not resolve these constraints.

## D. Evaluation and positioning

The evaluation would compare each eligible engine, the source-engine union, the current PQMigrate resolver and the proposed fused system. Source, binary and runtime tracks require separate ground-truth designs and denominators. Original independent labels must be locked before scoring, disagreement retained before adjudication, and failure or unsupported status must remain visible. Measure presence and role performance separately from recommendation correctness, abstention, review time, runtime coverage and resource cost. A majority vote among correlated detectors is not a substitute for independent gold.

The commercial hypothesis is that traceable role-specific review and migration blockers can reduce investigation effort. Existing enterprise products already advertise inventory, context and remediation-related workflows; uniqueness and superiority therefore require direct evidence. NIST's discovery/interoperability workstreams support the relevance of the problem, not an endorsement of this implementation [A6]. A claim of outperforming 95 percent of tools would require a defined tool population, comparable tasks, fair configurations and independently reproducible comparisons. It is neither a current result nor equivalent to 95 percent precision or a 95 percent confidence interval.

## Supplementary references

[A1] CSNP, CryptoScan, repository and documentation. https://github.com/csnp/cryptoscan

[A2] Semgrep, Community Edition. https://semgrep.dev/products/community-edition/

[A3] C. Meijer, V. Moonsamy, and J. Wetzels, "Where's Crypto?: Automated Identification and Classification of Proprietary Cryptographic Primitives in Binary Code," in Proc. USENIX Security, 2021, pp. 555-572. https://www.usenix.org/conference/usenixsecurity21/presentation/meijer

[A4] L. Piccolboni et al., CRYLOGGER, implementation and requirements. https://github.com/lucapiccolboni/crylogger

[A5] Semgrep, Rules License version 1.0. https://semgrep.dev/legal/rules-license/

[A6] NIST NCCoE, Migration to Post-Quantum Cryptography. https://www.nccoe.nist.gov/applied-cryptography/migration-to-pqc

[A7] PQMigrate, unscored baseline artifacts, revision 72dc7445c531bae2a54e488a5a97cf14c141bf90. https://github.com/Ratneshp1122/PQMigrate/tree/72dc7445c531bae2a54e488a5a97cf14c141bf90/experiments/semgrep_baseline

[A8] CSNP, CryptoScan Apache License 2.0. https://raw.githubusercontent.com/csnp/cryptoscan/main/LICENSE

[A9] CRYLOGGER, MIT License. https://raw.githubusercontent.com/lucapiccolboni/crylogger/master/LICENSE

[A10] Where's Crypto?, implementation README and tested requirements. https://raw.githubusercontent.com/wheres-crypto/wheres-crypto/master/README.md

[A11] GitHub Docs, Licensing a repository. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
