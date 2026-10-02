# ADR-003: Make D12 transformations preview-only

- **Status:** accepted
- **Date:** 2026-10-02

## Decision

D12 introduces one bounded Python AST transformation preview. It emits evidence and a unified diff but exposes no source-write API. Every request is bound to the target's expected SHA-256 and one line. D11 remains the authority for mutation eligibility, and D12 never marks a candidate eligible to apply.

## Rationale

A token replacement cannot distinguish executable calls from comments or strings and cannot detect stale input. AST selection plus exact-span validation addresses those narrow failure modes. It does not address application semantics, digest-size compatibility, peers, test adequacy, rollback, or operator authorization, so application belongs to later milestones.

## Consequences

- Supported preview: exact, unshadowed `hashlib.md5(...)` to `hashlib.sha256(...)`.
- Unsupported shapes fail closed rather than being guessed.
- Source files remain byte-for-byte unchanged.
- D13 must add isolated apply, verification, and rollback before any mutation path can be considered.
