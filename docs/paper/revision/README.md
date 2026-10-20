# Integrated manuscript: Draft 5

The current PDF is `../output/pdf/PQMigrate_ResearchPaper_Updated.pdf`. It integrates
the revised related work, methodology, limitations, evaluation status and IEEE
bibliography into one consistently numbered manuscript.

At the author's request on 21 October 2026, historical performance tables, plots
and numerical findings were removed. The 72-case study remains identified as a
single-author synthetic Python RSA pilot. Real-code evaluation is ongoing; no
replacement accuracy, precision, recall, TPR or agreement is claimed. The earlier
Draft 4 output has been replaced.

`manuscript.md` is the complete editable text; `front.md` and `back.md` are its
build inputs. The existing Markdown manuscript is synchronized with this text.
`source/Draft3.pdf` is an archival original, not the current paper.

`references.json` preserves 26 verified IEEE-style citations, primary sources,
supporting claims and verification limits. Full historical gate logs were not
independently verified; no gate-run result is asserted in the current PDF.
Publisher access limits for references 23 and 25 remain explicit in the audit.

## Rebuild

Use Python 3.12, reportlab 4.4.9 and pypdf 6.10.0 (see `build-environment.json`):

```text
python docs/paper/revision/build_manuscript.py
pdftoppm -scale-to 1200 -png docs/paper/output/pdf/PQMigrate_ResearchPaper_Updated.pdf /tmp/pqmigrate-updated
```

The builder creates the PDF, synchronizes the Markdown sources and records the
output SHA-256 in `build-audit.json`. Checks reject historical table markers,
numerical performance strings and old draft headers. All pages were rendered and
visually checked for clipping, layout continuity and readable references.

No A/B submissions were read. The separate baseline PR preserves unscored raw
runs and cannot establish accuracy before gold lock. Historical result pages
remain recoverable through Git history, rather than appearing in the current PDF.
