# Go RSA call-site observations (20 October 2026)

This engineering slice extends the Python call-site work on branch
`engineering/callsite-observations-2026-10-20`. It does not change the frozen
`bcfb5e4` pilot or supply a real-code accuracy estimate.

## Report contract

- `crypto/rsa` import detection remains a file-level `import_lead` with
  unknown role and an abstaining migration plan.
- Each Go RSA call linked by the bounded Tree-sitter resolver to a tracked key
  is a separate `linked_operation` at its own line and byte column. Multiple
  roles within one file no longer cause the entire file to lose call-level
  evidence, although the legacy file-level `infer_go_rsa_usage` API still
  abstains on conflicting roles for backward compatibility.
- Regex call matches by themselves remain candidates. They do not inherit a
  role from an RSA operation elsewhere in the file.
- Malformed Go source or an unavailable parser yields no linked operations.

The supported evidence is same-function key generation or explicit RSA key
parameter typing, selected RSA sign/verify/encrypt calls, and a narrow
crypto/rand-filled local buffer proxy for key transport. The proxy is not a
proof of application intent. Cross-function flows, field-level mutation,
wrapper identity, and arbitrary aliases are not resolved. Direct same-scope
rebinding of tracked names invalidates earlier evidence. Go source is parsed, never
executed. No generated migration patch is validated by this change.

## Verification

The full WSL test suite passed **121 tests** after this slice. Tests cover
import-only abstention and separately located signature and key-transport
calls in one Go file, plus rebinding abstention. The three new tests are
engineering regressions, not
independent evaluation cases. Research accuracy claims still require blind
annotation and adjudication on repository-separated real code.
