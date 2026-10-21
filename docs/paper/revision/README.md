# Original-format manuscript pending annotation results

The current PDF is `../output/pdf/PQMigrate_ResearchPaper_Updated.pdf`. Per the
author's latest instruction, it preserves the supplied original's formatting,
theory, wording, numbers and graphs byte for byte. The original input's filename
contained `Draft1_updated`, but its actual header identifies Draft 3.

Only numerical results and associated graphs are eligible for a future update,
and only after locked independent annotations provide a valid, comparable result.
The clean A packet is unreviewed. No completed, locked independent gold labels or
annotation accuracy measurements have been supplied. The separate Semgrep run
archives contain unscored engineering findings; they are not replacement scores.
Consequently, no improvement can currently be established and no number or graph
is changed. No A/B submission or prediction file is opened by the copy builder.

The earlier prose rewrite and the pending descriptive charts are not part of the
current paper. Earlier committed versions remain recoverable in Git history.
The existing repository Markdown scaffold is restored to its original revision.

Reproduce with Python and pypdf:

```text
python docs/paper/revision/build_manuscript.py
```

The builder verifies the original SHA-256, copies its exact bytes and records the
page count and unchanged-content status in `build-audit.json`. Exact byte equality
preserves all original fonts, layout, tables and graphs without re-typesetting.
