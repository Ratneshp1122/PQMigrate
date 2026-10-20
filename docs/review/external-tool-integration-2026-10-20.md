# External discovery integration: bounded first slice

## Purpose and trust boundary

PQMigrate's own source resolver remains responsible for operation and role
claims. External scanners can increase the **review queue**, but their output
cannot become a gold label, a proven operation, a migration plan, or a paper
accuracy result merely by being imported. The `external-triage` command reads
SARIF 2.1.0 from independently run tools, aligns source locations with an
optional PQMigrate JSON report, and marks every candidate
`unverified_external_lead` and `planning_eligible: false`.

This is the first integration boundary, not a claim that all external engines
are installed or optimized. At the initial WSL check on 20 October,
`cryptoscan`, `semgrep`, `rea`, and `go` were absent; Node and npm were present.
We subsequently ran a checksum-verified CryptoScan v1.4.0 binary from an
isolated `/tmp` directory on one already-exposed development checkout. See
[the pinned Go-JOSE comparison](cryptoscan-go-jose-exploratory-2026-10-20.md).
Semgrep and REA were not installed or run, and annotator packets were not altered.

## Tools and placement

| Tool | Useful input | PQMigrate treatment |
| --- | --- | --- |
| CryptoScan | Broad source/config/dependency discovery; SARIF output | Import locations as leads; independently verify source and role |
| Semgrep | Explicit, version-pinned crypto API rules; SARIF output | Import locations as leads and preserve rule/version provenance |
| REA | Evidence from a specified binary, packaged app, or recorded behavior | Out of scope now: no authorized target artifact is available |
| Where's Crypto?/CRYLOGGER | Binary or runtime observations | Later opt-in evidence lanes, subject to target authorization and reproducible installation |

The source projects describe CryptoScan's SARIF output and REA's native,
managed, JavaScript, and Go-binary inspection scope. REA's Go-binary metadata
inspection reveals build/module information, not automatically the meaning of
every cryptographic call. By user direction, REA is not installed, run, or
integrated without a suitable authorized binary or packaged app.

## Reproduction contract

Run the external tools separately, pin their versions and rules, keep their
full logs and outputs, and scan the **same checked-out source commit** as
PQMigrate. For example, after producing `cryptoscan.sarif`,
`semgrep.sarif`, and `pqmigrate.json`:

```bash
python3 cli.py external-triage /absolute/source/root \
  --pqmigrate-report /absolute/pqmigrate.json \
  --sarif cryptoscan=/absolute/cryptoscan.sarif \
  --sarif semgrep=/absolute/semgrep.sarif \
  --output /absolute/triage.json
```

The command does not execute the external tools or source project. It records
input SHA-256, reported driver names and versions, source Git HEAD when available,
whether it matches the PQMigrate report commit, skipped locations, candidates,
and same-line PQMigrate records. A missing or mismatched commit must be
resolved before using the queue in an evaluation. `external_only` is a review priority, **not** a
PQMigrate false negative: an independent human must determine whether the
location contains a valid cryptographic operation. Same-line overlap is not
semantic agreement. URI locations outside the selected root are skipped.

The SARIF bridge currently expects file paths resolvable in the same WSL
checkout and only the primary location of each SARIF result. URI-base IDs,
cross-host Windows paths, result flows, dependency-only findings, and REA
Evidence bundles need separate adapters. Missing or malformed evidence never
silently creates an operation or plan.

## Next experiment

1. Obtain pinned CryptoScan and Semgrep outputs on one already-exposed,
   permissioned repository; retain version, rules, commit, full logs, and
   timeout/failure accounting.
2. Triage external-only source anchors blind to PQMigrate advice and add
   validated misses to the engineering queue, **not** to the frozen pilot.
3. Keep REA and other binary/runtime lanes out of the present source-code
   evaluation. Reconsider them only if an authorized target artifact and a
   distinct research question become available.

Sources: [CryptoScan](https://github.com/csnp/cryptoscan),
[REA CLI/Evidence](https://github.com/morluto/rea/blob/main/docs/cli.md),
[Semgrep Community Edition](https://semgrep.dev/products/community-edition).
