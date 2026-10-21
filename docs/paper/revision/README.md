# Original paper with proposed integration work

The current paper is `../output/pdf/PQMigrate_ResearchPaper_Updated.pdf`.
The supplied original eight pages retain their exact decoded PDF page streams,
text and page geometry. Existing theory, numerical results, graphs, tables and
references are unchanged. An appendix adds the newly requested future
work in matching A4 two-column Times typography. It explicitly identifies the
four-tool integration and evaluation as proposed, not completed.

The separate professional proposal is
`../../proposals/PQMigrate_Integration_Proposal.pdf`; its repository path is
`docs/proposals/PQMigrate_Integration_Proposal.pdf`. It covers CryptoScan,
Semgrep, Where's Crypto? and CRYLOGGER, operating workflow, technical and license
gates, competitors, market-demand signals, evaluation, resources and a staged
delivery plan. The research plan is not a claim of outperforming 95 percent of
products. GitHub popularity is not treated as permission to reuse code or as
evidence of enterprise readiness.

`integration_sources.json` records 18 primary sources and what they support,
checked on 21 October 2026. Product descriptions are vendor documentation, not
independent performance tests. The earlier Explorer conversation was used only
to identify the intended scope. Relevant tool claims were checked against the
listed primary sources; unsupported rankings were excluded.
The available Phase-I report text was consulted for scope and limitations, not
treated as newly validated operational or accuracy evidence.

## Reproduce

Use Python with reportlab and pypdf:

```text
python docs/paper/revision/build_integration_proposal.py
python docs/paper/revision/build_manuscript.py
```

The paper builder uses installed Times New Roman fonts on Windows for its new
appendix, falling back to standard Times on other hosts. It never re-typesets the
original eight pages. `future_work.md` and `proposal_content.json` are editable
content sources. `build-audit.json` records source/output hashes and the original
page stream digests. The proposal is a PDF; no Word-rendering workflow is needed.

No annotator submission was read. The clean A packet remains unreviewed and the
Semgrep observations remain unscored. A defined tool population, independent
locked gold and comparable held-out tasks are prerequisites for superiority
claims. No source or runtime analysis was executed for this proposal.
