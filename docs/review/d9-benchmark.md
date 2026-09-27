# D9 — PQMigrateBench Pilot

## Scope and claim boundary

PQMigrateBench v0.1 is a **single-author synthetic pilot** for the bounded Python RSA role resolver. It is not an independently labelled corpus, it does not evaluate Go, the full scanner registry, the dashboard, or patch safety, and its metrics must not be presented as product-wide accuracy.

The pilot contains 72 cases across `train` (44), `dev` (14), and held-out `test` (14) splits. The resolver is rule-based and does not train on the train split; the split exists to prevent iterative fixes from silently consuming every evaluation case.

## Annotation unit

One case is one source snippet containing zero or more RSA-related observations. The gold unit is the semantically relevant operation in that snippet:

- `is_operation`: whether an unambiguous RSA operation exists;
- `role`: signature, key transport, encryption, or unknown;
- `operation`: sign, verify, encrypt, decrypt, or unknown;
- `protocol_context`: JWT or unknown;
- `confidence`: direct, inferred, or ambiguous.

Conflicting roles are labelled unknown because the current resolver returns one bounded result per snippet and ADR-001 requires abstention. Imports and unused key generation are negative/inventory controls, not confirmed operations. Invalid syntax is tagged `parse_failure` and counted separately.

## Labelling procedure

1. Read the complete snippet without executing it.
2. Identify the key object and its exact consumer.
3. Label the operation only when object identity and call semantics are explicit.
4. Use key transport only when RSA encrypts a generated session secret.
5. Use encryption when RSA encrypt/decrypt is explicit but transport purpose is not established.
6. Use unknown for import-only, unused generation, conflicting roles, unrelated keys, or unsupported ambiguity.
7. Record a short rationale before running the evaluator.

The committed labels were authored with the dataset and have not received a second independent adjudication. Future paper results require two labelers, blinded predictions, disagreement tracking, and adjudication.

## Dataset composition

- 12 direct signature cases;
- 8 JWT signature cases;
- 12 key-transport cases;
- 8 asymmetric-encryption cases;
- 16 negative controls;
- 4 parse failures; and
- 12 valid but deliberately unsupported parameter/alias-flow operations.

Parameterized variants exercise import aliases, operations, scopes, algorithms, and secret sources. They are correlated synthetic variants, not 72 independent applications.

## Metrics

Operation detection reports TP, FP, FN, TN, precision, recall, and F1 on cases tagged `evaluated`. Parse failures are reported separately. Role evaluation on gold operations reports:

- answer coverage = answered / gold operations;
- accuracy among answered = correct roles / answered; and
- end-to-end role accuracy = correct roles / gold operations.

Every run writes raw per-case predictions and mismatch types. Undefined ratios serialize as `null`; they are never replaced by zero.

## Reproduction

From the repository parent:

```bash
python3 -m pqc_migration_tool.benchmarks.evaluate \
  --dataset pqc_migration_tool/benchmarks/pqmigratebench_v0_1.jsonl \
  --output pqc_migration_tool/review-artifacts/latest/d9-benchmark-results.json
```

Use `--split test` for the held-out slice. The result records the dataset SHA-256, evaluator commit, raw predictions, errors, split metrics, and the scope disclaimer.

