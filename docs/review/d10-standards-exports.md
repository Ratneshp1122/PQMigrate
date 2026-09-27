# D10 — standards-based export

D10 adds two validated interchange formats without changing the canonical PQMigrate report schema or claiming automatic remediation:

- SARIF 2.1.0 Errata 01 for code-scanning ingestion.
- CycloneDX 1.7 CBOM for cryptographic-asset inventory.

Every document is checked against a pinned official schema before it is returned or written. Validation is offline and reproducible through `scripts/review_smoke.sh`.

## Commands

Generate a format directly from a scan:

```bash
python3 cli.py scan tests/fixtures/review --format sarif --output review.sarif.json
python3 cli.py scan tests/fixtures/review --format cbom --output review.cdx.json
```

Convert the same canonical JSON report into both formats so the scan ID and decision records stay identical:

```bash
python3 cli.py export report.json --format sarif --output report.sarif.json
python3 cli.py export report.json --format cbom --output report.cdx.json
```

The scanner still returns policy exit code `1` when critical or high findings exist. A successful `export` conversion returns `0`; malformed input or schema-invalid output returns `1`.

## SARIF mapping

| PQMigrate field | SARIF 2.1.0 field |
|---|---|
| Rule ID and rule version | `tool.driver.rules[]` and `result.ruleId` |
| Security status | `result.level` (`error`, `warning`, or `note`) |
| Primitive, role, operation, target, outcome | `result.message.text` |
| File, line, zero-based scanner column | `physicalLocation`; exported column is one-based |
| Finding ID | `partialFingerprints.pqmigrateFindingId` |
| Confidence, trace ID, blockers, standards refs | `result.properties` |
| Scan/rules/schema/source versions | `invocation.properties` |

Source snippets are deliberately excluded. Locations use paths relative to a shared source root where possible.

## CycloneDX CBOM mapping

Each finding becomes one CycloneDX component with `type: cryptographic-asset`. This preserves per-use role and decision evidence even when several findings name the same primitive.

| PQMigrate field | CycloneDX 1.7 field |
|---|---|
| Finding ID | Component `bom-ref` |
| Primitive | Component `name` |
| Algorithm/protocol classification | `cryptoProperties` |
| File and line | `evidence.callstack.frames[]` |
| Role, status, confidence, rule, trace, blockers | Namespaced component `properties` |
| Scanned project | Metadata application component |
| Supported-pattern inventory limitation | Composition aggregate `incomplete` and `pqmigrate:scope-note` |

RSA key transport is represented as the `pke` algorithm primitive; signature use is represented as `signature`. TLS and SSH findings are represented as protocol assets when that context is established.

## Schema provenance

- OASIS SARIF 2.1.0 Errata 01 schema: <https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/schemas/sarif-schema-2.1.0.json>
- CycloneDX 1.7 schema from specification release 1.7.1: <https://raw.githubusercontent.com/CycloneDX/specification/1.7.1/schema/bom-1.7.schema.json>

Pinned copies and source notes are under `exporters/schemas/`.

## Review-safe limitations

- Export compliance does not expand scanner coverage or prove inventory completeness.
- The CBOM composition is explicitly marked incomplete.
- SARIF severity is a deterministic interoperability mapping, not a newly calibrated risk model.
- No source snippet is exported; downstream users must access the reviewed repository to inspect code.
- Neither format authorizes a patch. `patch_available=false` remains visible in the exported evidence.
- Import behavior in a particular third-party platform remains integration work; D10 verifies schema validity and deterministic mapping locally.
