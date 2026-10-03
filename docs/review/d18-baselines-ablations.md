# D18 — Same-corpus baselines and ablations

D18 compares five deterministic systems on the exact 72-case PQMigrateBench v0.1 corpus: unsafe lexical primitive lookup, method-name AST only, full inference without session-secret flow, full inference without protocol context, and the complete bounded pipeline.

The experiment preserves identical case IDs, split assignments, gold labels, denominators and error accounting. It reports operation precision/recall/F1, answer coverage, end-to-end role accuracy, exact operation/role accuracy, labelled protocol-context accuracy, raw predictions and deltas against the full pipeline.

The purpose is explanatory, not promotional: primitive lookup exposes high recall with false positives; AST-only exposes the cost of ignoring receiver identity; removing secret flow collapses key transport into encryption; removing context removes JWT recognition. Results remain a single-author synthetic Python RSA pilot and are not product-wide accuracy.

Run `bash scripts/run_d18_baselines.sh`.
