# D4 — bounded Go semantic role analysis

## Acceptance result

D4 is complete for its declared bounded scope. Go primitive discovery remains
regex-based, while RSA role inference uses the Tree-sitter Go grammar to build
a real syntax tree. Target repositories are read and parsed but never compiled,
imported, or executed.

## Supported evidence

- normal and aliased `crypto/rsa` imports;
- RSA private keys produced by `rsa.GenerateKey` or `rsa.GenerateMultiPrimeKey`;
- explicitly typed `*rsa.PrivateKey` and `*rsa.PublicKey` parameters;
- public-key expressions derived from a tracked private key;
- `SignPKCS1v15`, `SignPSS`, `VerifyPKCS1v15`, `VerifyPSS`, and key `.Sign()`;
- `EncryptOAEP` and `EncryptPKCS1v15` with a same-function byte buffer filled
  by `crypto/rand.Read` or `io.ReadFull(rand.Reader, ...)`;
- import-alias shadowing, unrelated keys, malformed source, and conflicting
  roles as explicit abstention cases.

## Claim boundary

The resolver is not interprocedural and does not infer arbitrary interfaces,
wrappers, struct fields, reflection, generated code, build-tag selection, or
cross-file flows. RSA encryption is classified as `KEY_TRANSPORT` only when the
encrypted argument is a tracked random session secret. Other linked encryption
is reported as context-dependent encryption, not silently promoted to transport.

Any parser dependency failure or unsupported flow returns `UNKNOWN`. D4 does
not authorize patching; the independent D11 five-condition gate remains in
force and all current reports remain non-mutating.

## Reproduction

```bash
python3 -m pytest -q tests/test_go_semantic.py
scripts/validate_d0_d11.sh --strict
```

The ten-case focused suite covers aliased and typed-parameter signatures, key
transport, import-only, unrelated-key, alias-shadowing, conflicting-role,
malformed-source, dependency availability, and canonical-report integration.
