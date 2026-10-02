# D14 — two-party interoperability laboratory

- **Version:** `2026.10.02-d14.1`
- **Selected migration:** controlled MD5-to-SHA-256 digest contract
- **Status:** implemented with a bounded compatibility claim

D14 runs two independent protocol endpoints over an OS socket pair. The client advertises supported digest modes, the server selects its preferred common mode, the client returns a digest proof, and the server verifies it. The repeated matrix covers matching legacy peers, matching migrated peers, a transitional dual-mode peer, legacy fallback, no-common-mode failure, and a tampered-digest failure.

Every scenario records its denominator, success/failure count, selected mode, visible failure status, duration distribution, wire bytes, digest size, environment, and raw samples. Mismatched peers must fail as `no_common_mode`; an invalid digest must fail as `digest_mismatch`.

## Claim boundary

This is interoperability evidence for the exact controlled digest contract selected in D12. It is not a classical/PQC hybrid KEM matrix and does not establish TLS, SSH, JWT, certificate, database, external-provider, or production compatibility. The roadmap's classical/hybrid requirement is therefore not claimed for this transformation.

## Reproduce

```bash
python3 cli.py interop-lab --repeats 20 --output review-artifacts/latest/d14-interoperability.json
```
