# D13 — isolated verification and rollback evidence

- **Version:** `2026.10.02-d13.1`
- **Status:** implemented with a bounded verification claim
- **User source mutation:** disabled

## What D13 establishes

D13 takes the hash-bound D12 preview, materializes it only inside a disposable temporary directory, runs a time-limited Python syntax compilation, rescans the transformed AST, verifies that the original file hash is unchanged, and removes the disposable directory. Timeout, verifier startup failure, failed syntax, failed rescan, stale source, or failed cleanup produces blocker codes and no apply eligibility.

The supported check is deliberately narrow: one direct Python `hashlib.md5(...)` previewed as `hashlib.sha256(...)`. The evidence status `verified_bounded` means the preview remained syntactically valid and structurally exact in the disposable copy. It does not mean the migration is semantically correct.

## Isolation boundary

The current boundary is a new temporary filesystem tree containing only the selected source path. The verifier uses an argument-vector subprocess, a 1–60 second timeout, captured output, and a fixed `python -m py_compile` command. It accepts no arbitrary shell command.

This is not a container, VM, syscall sandbox, network namespace, or full project build. D13 therefore keeps `eligible_for_apply=false`. Adequate project tests and D14 interoperability evidence remain unresolved.

## Use

```bash
sha256sum sample.py
python3 cli.py verify-preview sample.py \
  --project-root . \
  --expected-sha256 <64-hex-digest> \
  --line <line-number> \
  --timeout 10 \
  --output review-artifacts/latest/d13-verification.json
```

## Acceptance evidence

`tests/test_d13_isolated.py` covers the success path, original-source preservation, source-boundary refusal, D12 refusal propagation, timeout cleanup, invalid timeout refusal, and CLI artifact generation. `scripts/run_d13_verification.sh` regenerates the bounded evidence and verifies the fixture's hash before and after.
