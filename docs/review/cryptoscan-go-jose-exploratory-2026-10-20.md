# Exploratory CryptoScan → PQMigrate triage on Go-JOSE

Date: 20 October 2026. This is **engineering discovery**, not a benchmark,
gold annotation, accuracy/TPR measurement, or paper result. It used an
already-exposed development repository. Independent annotators did not supply
these labels and must not see tool predictions while labeling.

## Pinned inputs and commands

- Source: `go-jose__go-jose` checkout at
  `25b55feb059b8b08e16a73c601c8b80571fa5208`.
- CryptoScan: official v1.4.0 Linux AMD64 release (`11f0e46`), archive SHA-256
  `49aa043bd3f46927efa8ee89a2344d30f2ec351ae9e0cf2791ac8206b45be19d`,
  matched against the release API digest before extraction. No system install.
- PQMigrate implementation: engineering commit
  `31eb56175f88537fa6bfc9db1aa96d9a5ad9670e`. The JSON report records
  the target source commit, not the PQMigrate implementation commit, so both
  identities are stated here.

```bash
SRC=/home/ratneshp0411/pqmigrate-real-code-study/repositories/go-jose__go-jose
EVID=/home/ratneshp0411/pqmigrate-real-code-study/external-triage/2026-10-20-go-jose
/tmp/pqmigrate-cryptoscan-v1.4.0/cryptoscan scan "$SRC" --format sarif --output "$EVID/pqmigrate-go-jose-cryptoscan-v1.4.0.sarif"
/tmp/pqmigrate-cryptoscan-v1.4.0/cryptoscan scan "$SRC" --format json --output "$EVID/pqmigrate-go-jose-cryptoscan-v1.4.0.json"
/home/ratneshp0411/venv/bin/python /home/ratneshp0411/pqc_migration_tool/cli.py scan "$SRC" --format json --output "$EVID/pqmigrate-go-jose-report.json" --quiet
/home/ratneshp0411/venv/bin/python /home/ratneshp0411/pqc_migration_tool/cli.py external-triage "$SRC" --pqmigrate-report "$EVID/pqmigrate-go-jose-report.json" --sarif cryptoscan="$EVID/pqmigrate-go-jose-cryptoscan-v1.4.0.sarif" --output "$EVID/pqmigrate-go-jose-external-triage.json"
```

Both scanners returned exit code 1 while writing valid output. Preserve that
exit status as observed; do not silently count it as success or a parser
failure. The outputs exist and parse, but an exit-1 reason was not isolated.

## Observations, not performance estimates

| Item | Output |
| --- | ---: |
| CryptoScan files scanned (its scope) | 82 |
| CryptoScan SARIF results | 768 |
| Distinct source-line locations after triage grouping | 736 |
| PQMigrate files scanned (Go scope) | 73 |
| PQMigrate findings after this engineering slice | 73 |
| PQMigrate import leads / unknown-role operation candidates / linked roles | 61 / 8 / 4 |
| Triage external-only / same-line inventory overlap / same-line linked overlap | 690 / 42 / 4 |

The file scopes differ. CryptoScan findings can be declarations, comments,
tests, configuration, or duplicate matches; PQMigrate findings include
imports. A line-location union is not an operation-level denominator. The
690 external-only locations are **unreviewed leads**, not 690 verified misses.
CryptoScan v1.4.0 documents occurrence-specific SARIF rule IDs; the bridge
groups by source path and line, not by rule ID.

The triage led to a bounded Go resolver improvement. A same-file struct with
an explicitly typed `*rsa.PrivateKey`/`*rsa.PublicKey` field, used through a
method receiver, now supplies key-identity evidence. On this checkout it
linked four RSA sign/verify calls at `asymmetric.go:292,294,332,334`.
RSA encrypt calls at lines 199, 201, 203 and decrypt calls at 249, 254, 257
are observed with their operations but **unknown roles and abstaining plans**:
the source evidence here is insufficient to conclude data encryption versus
key transport. Direct receiver-field writes invalidate earlier identity.
This is source inspection by the developer, not independent adjudication.

Complete outputs were preserved outside the repository at `EVID` above; they
were not published to GitHub or shared with blind annotators. SHA-256 values:

```text
1155cc43df7f7216976fc342187b834a130cf1336a52221e225e15a01b222374  pqmigrate-go-jose-cryptoscan-v1.4.0.sarif
f6af9522901422533a72093ed4d743c49284d2ab2cbdc3d6af50b8a10a0cec27  pqmigrate-go-jose-cryptoscan-v1.4.0.json
6a8ea9dc8480ea9d56f1e3314c8bf1415f0045b690c5f7d2afa438524c44b6fb  pqmigrate-go-jose-report.json
c2ae47a62d3dd42ad9caa8306513daaaf3629d2ee1e70401b7caa188541e6a63  pqmigrate-go-jose-external-triage.json
```

See the [official CryptoScan v1.4.0 release notes](https://github.com/csnp/cryptoscan/releases/tag/v1.4.0)
for documented scanner and SARIF limitations. This comparison does not test
REA; that lane is excluded because there is no authorized target artifact.
