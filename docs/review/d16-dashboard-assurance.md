# D16 — Dashboard pages E–G

D16 extends the loopback-only, read-only workbench with a hash-bound patch preview, assurance ledger, deterministic exports, and optional two-manifest comparison.

Run `python3 cli.py dashboard --input review-artifacts/latest/three-fixture-report.json --compare previous.json`. Page E shows D12 scope, blockers, risk and unified diff without an apply action. Page F joins D12–D14 evidence and renders missing work as `not_run`, never green. Page G exports JSON, SARIF, CBOM or Markdown and distinguishes new, resolved and unchanged finding IDs from coverage changes.

The server accepts no mutation methods, binds only to loopback, uploads nothing, and does not claim that bounded digest compatibility proves PQC/hybrid interoperability.
