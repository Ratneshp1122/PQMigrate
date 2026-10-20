# Python call-site observations (20 October 2026)

This development change is separate from the frozen `bcfb5e4` pilot. It does
not revise that commit, its evidence, or the independent annotation packets.

## Output contract

- A recognized RSA import remains an `import_lead` with unknown role and an
  abstaining plan. Its source location stays on the import statement.
- A supported RSA call is a separate `linked_operation` at the call's line and
  column. A typed RSA parameter yields `inferred` confidence; a tracked local
  RSA key can yield `direct` confidence. Neither confidence value is a
  calibrated probability or a proof of the runtime object.
- Repeated call sites are retained, including distinct calls on one line.
  Repeated imports of one primitive in one file remain one inventory lead.
- Registered hash calls through import aliases are emitted at each call site.
  Function-local aliases and rebound names are not allowed to leak into
  unrelated scopes. This is bounded alias handling, not sound Python analysis.
- Report IDs include the source column and match type, avoiding same-line
  collisions. The canonical report's `total_findings` equals its record count.
- A safe conventional hash is `context_dependent`, not `standardized_pqc`.
  The latter status is reserved for recognized PQC KEM, signature, or hybrid
  families in this reporting path.

## Supported and unsupported evidence

The RSA resolver recognizes same-scope local private-key generation, explicit
`cryptography` RSA private/public parameter types, `.sign`, `.verify`,
`.encrypt`, `.decrypt`, and bounded `jwt.encode` RS/PS signing. Its
key-transport conclusion still depends on the local random-value proxy and
requires manual review. Generated key and random-value variables with
same-scope rebinding are conservatively not tracked. It does not establish
arbitrary wrappers, cross-function or cross-file data flow, runtime type
identity, or a safe PQC transformation. Go call-site reporting is unchanged
in this slice.

## Verification and interpretation

Run from a checkout with the project parent on `PYTHONPATH`:

```bash
/home/ratneshp0411/venv/bin/python -m pytest -q /home/ratneshp0411/pqc_migration_tool/tests
```

The WSL run passed 118 tests. A read-only smoke check on the previously
inspected PyJWT revision emitted separate RSA calls at `jwt/algorithms.py`
lines 683 and 688. A development scan over the three already-exposed Python
repositories emitted 19 findings for PyJWT (15 import leads, four linked
calls), 22 for Paramiko (17 import leads, five registered calls), and 116 for
pyca/cryptography (113 import leads, one linked call, two registered calls).
These are scanner output counts on purposively selected development sources,
not unique-operation counts, recall, precision, TPR, or held-out results.
Human review and independent-source anchors remain required.
