# ADR-002: Five-condition fail-closed patch gate

- **Status:** Accepted for D11; no transformation approved
- **Date:** 2026-09-27
- **Policy version:** `2026.09.27-d11.1`

## Context

A migration recommendation is not evidence that a source mutation is safe. Role inference, provider support, interoperability, test adequacy, and operator authorization are independent facts. The legacy patch skeleton could otherwise be activated by a crafted report.

## Decision

PQMigrate uses five three-valued conditions: known role, supported construction, interoperable peers, tests available, and operator authorization. Only five `true` values permit theoretical eligibility. A false or unknown condition refuses mutation. Eligibility fields supplied inside a scan report are not trusted as authority.

At D11, current evidence can establish only bounded role knowledge. The other four conditions remain unknown, so no current report is eligible. The legacy mutation path stays quarantined.

## Consequences

- Current scans and exports remain advisory-only.
- A crafted `patch_available=true` value cannot authorize mutation.
- Missing verification tools fail closed.
- D12 must add preview-only transformations individually and may not bypass this policy.
- D13 must supply isolated verification evidence; D14 must supply protocol interoperability evidence where relevant.
