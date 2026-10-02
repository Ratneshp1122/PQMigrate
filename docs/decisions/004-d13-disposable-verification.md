# ADR-004: Verify previews only in disposable copies

- **Status:** accepted
- **Date:** 2026-10-02

## Decision

D13 may materialize a D12 preview only beneath a newly created temporary directory. It runs a fixed, time-limited syntax check, rescans the exact AST call, removes the directory in a `finally` path, and confirms that the original source hash is unchanged. It does not expose an apply-to-checkout operation or accept arbitrary test commands.

## Consequences

- Verification failures and timeouts retain rollback evidence and fail closed.
- The user checkout remains untouched.
- Filesystem-copy isolation is reported accurately and is not described as a security sandbox.
- Full project tests, behavioral correctness, digest-size compatibility, and interoperability remain future evidence requirements.
