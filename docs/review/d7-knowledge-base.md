# D7 versioned YAML knowledge base

## Outcome

Migration planning now reads `knowledge/migration_rules.yaml` instead of using hardcoded primitive branches in `resolver/planner.py`.

Each rule contains:

- stable rule ID and priority;
- primitive fragments and allowed semantic roles;
- advisory migration family and standard;
- mandatory manual-intervention reason;
- explicit blocker codes;
- primary standards references.

The report records both the matched `rule_id` and knowledge-base `rule_version`.

The active rules can be validated and listed without running a scan:

```bash
python3 cli.py list-rules
python3 cli.py list-rules /path/to/candidate-rules.yaml
```

Set `PQMIGRATE_KNOWLEDGE_PATH` to test an alternate valid rule file without changing application code.

## Safety boundary

D7 rules cannot authorize mutation. The loader rejects any rule whose `patch_available` value is not `false` or whose `requires_manual_intervention` value is not `true`. Patch eligibility remains a later assurance milestone.

The loader also rejects:

- duplicate rule IDs;
- missing schema or rules versions;
- unknown roles or protocol contexts;
- unknown or mismatched security statuses;
- empty primitive predicates;
- missing blocker codes or standards references;
- malformed YAML.

Every classical rule also includes an allowed security-status predicate. This prevents a substring such as `dsa` from applying a classical-signature rule to an already standardized `ML-DSA` observation.

## Current rule families

| Rule | Role | Advisory target |
|---|---|---|
| `RSA-SIGNATURE-001` | Signature | ML-DSA assessment |
| `RSA-KEY-TRANSPORT-001` | Key transport | ML-KEM-based KEM/DEM redesign |
| `RSA-ENCRYPTION-001` | Unresolved-purpose RSA encryption | Manual KEM/DEM assessment |
| `HYBRID-KEY-ESTABLISHMENT-001` | Key establishment | RFC 10024 hybrid-group assessment |
| `CLASSICAL-SIGNATURE-001` | ECDSA, EdDSA, or DSA signature | ML-DSA or SLH-DSA assessment |
| `SYMMETRIC-AES-001` | Symmetric encryption | AES-256 assessment |
| `HASH-MD5-001` | Hash | SHA-256 or SHA3-256 assessment |
| `HASH-SHA1-001` | Hash | SHA-256 or SHA3-256 assessment |
| `HASH-SHA256-001` | Hash | Retain or assess a larger SHA-2 output |

## Verification

```bash
cd /home/ratneshp0411
/home/ratneshp0411/venv/bin/python3 -m pytest -q \
  pqc_migration_tool/tests/test_knowledge_base.py
```

The full review evidence is regenerated through `scripts/review_smoke.sh`.
