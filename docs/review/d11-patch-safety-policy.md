# D11 — patch safety and approval policy

- **Policy version:** `2026.09.27-d11.1`
- **Status:** proposed and technically enforced as fail-closed
- **Automatic mutation approval:** **not granted**
**Required approvers before any transformation is enabled:** faculty/security reviewer and repository owner/operator

This policy defines when PQMigrate may eventually preview or apply a source transformation. D11 does not approve any rewrite. The current scanner and planner remain advisory, and current reports cannot make the patch gate pass.

## Safety claim

For a candidate finding `x`, define:

- `K(x)`: its cryptographic role is known from linked evidence.
- `S(x)`: the exact replacement construction is approved and supported by the actual provider and protocol.
- `I(x)`: every relevant peer, stored artifact, wire format, and deployment dependency is interoperable.
- `T(x)`: adequate tests exist and can run in an isolated, bounded environment.
- `O(x)`: an authenticated operator explicitly authorizes mutation of an owned disposable copy.

Every condition has one of three values: `true`, `false`, or `unknown`.

```text
Eligible(x) = K(x) ∧ S(x) ∧ I(x) ∧ T(x) ∧ O(x)
```

Eligibility is true only for the single `(true, true, true, true, true)` assignment. Any false or unknown value refuses mutation. The exhaustive D11 test evaluates all `3^5 = 243` assignments and confirms exactly one theoretical eligible assignment.

This proves only a decision-gate invariant. It does not prove that detection, a recommended construction, a generated patch, or a deployment is secure.

## Evidence authority

The input report is untrusted for mutation authority. A report field such as `patch_available=true`, `requires_manual_intervention=false`, or an embedded all-true eligibility object is insufficient. Current D11 assessment derives only `K(x)` from typed role evidence and keeps `S`, `I`, `T`, and `O` unknown.

Future evidence must come from independent trusted controls:

| Condition | Minimum acceptable evidence | Current state |
|---|---|---|
| `K` known role | Identity-linked operation trace with no conflicting use | Available only for bounded cases |
| `S` supported construction | Version-pinned transformation, provider capability, standards reference, and reviewer approval | Unknown; no rewrite approved |
| `I` interoperable peers | Enumerated consumers plus observed protocol negotiation and artifact compatibility | Unknown |
| `T` tests available | Declared commands, isolated execution, timeout/resource limits, expected assertions, rescan, and rollback test | Unknown |
| `O` operator authorized | Explicit per-run approval bound to repository, commit, diff, and expiry | Unknown |

## Mandatory refusal conditions

Mutation must be refused when any of these applies:

- role, key identity, alias flow, or consumer is unresolved or conflicting;
- a private key is serialized, exported, shared, loaded externally, or managed outside the scanned boundary;
- the change affects a public API, certificate, key identifier, signature format, stored ciphertext, database schema, wire protocol, or external peer without compatibility evidence;
- the target provider, library version, construction, parameters, or standards status is not pinned and approved;
- a home-grown hybrid combiner or category-changing substitution is proposed;
- generated, vendored, minified, signed, or third-party code would be changed;
- the report source commit does not match the disposable working copy, or the target span has changed;
- tests are missing, fail, time out, cannot start, or execute outside the approved isolation boundary;
- rollback cannot be demonstrated before mutation;
- operator authorization is missing, stale, broader than the reviewed diff, or applies to a different repository/commit;
- secrets or source snippets would be exported to an external service.

## Transformation policy

No transformation is approved at D11. In particular:

- generic RSA-to-ML-KEM replacement is forbidden;
- RSA signing must not map to ML-KEM;
- RSA encryption/key transport requires a protocol-level KEM/DEM redesign, not a token replacement;
- changing `AES-128` text to `AES-256` does not establish correct key generation, storage, rotation, or protocol compatibility;
- replacing `md5` or `sha1` textually is unsafe when digest length, protocol fields, file formats, or compatibility contracts matter.

D12 may introduce preview-only, AST-aware transformations one construction at a time. Each transformation needs its own approved preconditions, negative fixtures, exact diff, and rollback behavior before this document can list it as supported.

## Required workflow for a future patch

1. Pin repository identity and source commit; create a disposable clean worktree.
2. Rescan and bind the finding, decision trace, rule version, and source span to that commit.
3. Evaluate the five conditions from independent evidence and record blocker codes.
4. Generate a preview diff only; do not write to the user checkout.
5. Obtain per-diff operator authorization.
6. Apply only in the disposable worktree.
7. Run isolated syntax/build/unit/integration checks, rescan, and required interoperability observations.
8. Roll back on any failure, timeout, missing tool, or inconclusive result.
9. Preserve commands, outputs, hashes, environment versions, and the final decision.
10. Promote the patch only through a separate reviewed commit or pull request.

## Existing prototype audit

The pre-D11 patch skeleton performed line-oriented string replacement and adjacent `.bak` writes. Its risks include stale line numbers, replacements inside unrelated text, incomplete rollback scope, mutation in the source checkout, and lack of provider/protocol evidence. The verification skeleton also previously treated a missing `pytest` executable as success.

D11 places the skeleton behind `assess_record()`, which ignores self-asserted report eligibility and currently leaves four conditions unknown. Therefore it cannot reach its write path. A missing test runner now fails closed. These controls quarantine legacy code; they do not make it production-safe.

## Review and approval record

| Decision | Reviewer | Date | Scope/version | Notes |
|---|---|---|---|---|
| Policy reviewed | _pending_ | _pending_ | `2026.09.27-d11.1` | Automatic mutation remains disabled until signed review |
| First transformation approved | _none_ | _none_ | _none_ | D12 work must not infer approval |

Any policy edit, new transformation, provider/library version change, or changed trust boundary requires a new policy version and renewed approval.
