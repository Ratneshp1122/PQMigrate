# D8 — Migration Decision Trace and Priority

## Exit criteria

D8 is complete when every generated migration plan:

1. links to the finding ID, source span and containing Git commit when available;
2. records detection, role inference, rule matching, blocker assessment and final decision;
3. emits a deterministic trace ID for equivalent semantic input;
4. lists unresolved fields instead of inventing missing context;
5. exposes categorical priority axes without presenting a probability; and
6. remains advisory-only (`patch_available=false`).

## Decision paths

- `recommend`: a versioned YAML rule matched the typed finding. This is still a conditional recommendation requiring manual intervention and blocker resolution.
- `abstain`: the role was ambiguous or no enabled rule matched. No migration target is asserted as safe.

## Priority policy

`cryptographic_urgency` is derived only from `SecurityStatus`. `evidence_strength` is the original confidence class. `migration_effort` is supplied by the matched rule. `data_exposure` is always `unknown` in D8 because source inspection cannot establish business sensitivity or retention. Abstentions always have `overall_review_priority=manual_review`; other findings inherit the urgency band.

This policy is deliberately inspectable and is not an empirical risk model.

## Reproducibility

The trace ID hashes canonical semantic inputs: finding identity and location, source commit when available, primitive, role, operation, status, confidence, protocol context, decision outcome, selected rule/version, blockers and target. It excludes scan timestamp and scan ID. Two equivalent pinned scans therefore preserve the same decision trace IDs.
