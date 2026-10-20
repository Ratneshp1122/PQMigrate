# Draft 4 revision and evidence audit

This revises the supplied eight-page Draft 3 PDF (14 October 2026) and the existing
Markdown manuscript scaffold. The source filename supplied by the author contained
`Draft1_updated`; its actual header is Draft 3. `source/Draft3.pdf` preserves that
input, SHA-256 `6cde5495e7cc16b88c274e78a6f75e244401465c894f52f61dff4e61fbbaf2d7`.

The revised manuscript is `../output/pdf/PQMigrate_Draft4.pdf`. `front.md` and
`back.md` are editable revised prose. Pages 4-6 are copied verbatim from the source
PDF, including Tables II-V, figures, historical qualifications and Draft 3 headers.
Their decoded PDF content streams and extracted text must remain identical. This
preserves the original result tables exactly; the older Markdown scaffold's table
is also unchanged. No new result is promoted to the paper on a better-only basis.

`references.json` contains 26 IEEE-style entries, supporting claims, primary URLs
and verification scope, checked 21 October 2026. Important corrections include the
actual CryptoAPI-Bench artifact, full SARIF standard rather than errata-only text,
RFC 9964 title/date, CryptoGuard author-version date, and explicit distinctions
between standards, author manuscripts, product documentation and measured results.
Claims about other tools are limited to their documented tasks; no numerical
comparison is borrowed from their evaluations.

Verification limitations are explicit: publisher metadata/author retrospective
support reference 25; full publisher text for reference 23 was limited, with the
rule-of-three attribution cross-checked against the cited NIST presentation.
Neither reference supplies an empirical guarantee for this purposive pilot. The
source at evaluated commit `bcfb5e40fbc8eb74e1c919114f54031d03ab44e9` supports
implementation/corpus statements. External full historical gate logs were not
available for independent verification; preserved historical claims are qualified
in the new prose, rather than falsely certified. The corpus file SHA-256 is
`293fee315c4fbcb95f0d071615ce54a7ac6c9b8b89783a832832c15e3697603b`.

## Rebuild and verify

Use Python 3.12+ with `reportlab==4.4.9` and `pypdf==6.10.0` (the actual build
environment is recorded in `build-environment.json`; use its versions if these
example pins differ):

```text
python docs/paper/revision/build_manuscript.py
pdftoppm -scale-to 1200 -png docs/paper/output/pdf/PQMigrate_Draft4.pdf /tmp/pqmigrate-draft4
```

The builder fails if the front material does not occupy exactly three pages or
the protected result-page streams/text differ. `build-audit.json` records whole
PDF and protected-page hashes. PDF metadata timestamps may vary on rebuild;
protected content hashes must not. Visual review must check all rendered pages
for clipping and readable references. No target repository code is executed.

## Ongoing study

The revised SOP protocol supersedes draft targets presented as if achieved: two
eligible reviewers independently inspect the same 500 anchors, use separate
calibration, freeze assigned production IDs beforehand, and lock original labels
before comparison/adjudication. The 240-anchor ordinary-source packet is a
separate stage. No submissions were opened, no individual cases were discussed
with reviewers, and no real-code precision, recall, TPR or agreement is claimed.
Operation-unit questions are in [issue 1](https://github.com/Ratneshp1122/PQMigrate/issues/1).
Ratnesh instructed use of the reviewer SOP taxonomy. Any future accuracy comparison
still requires locked gold, comparable units and full failure accounting.
