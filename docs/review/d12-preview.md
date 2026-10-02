# D12 — AST-aware transformation preview

- **Version:** `2026.10.02-d12.1`
- **Status:** implemented, preview only
- **Source mutation:** disabled
- **First bounded construction:** direct Python `hashlib.md5(...)` call to `hashlib.sha256(...)`

## Claim and boundary

D12 can identify one direct call through Python's AST, validate its exact UTF-8 source span, bind the request to the current file SHA-256, and emit a unified diff. It does not write the source file, authorize application, prove compatibility, or claim that SHA-256 is the correct replacement for every MD5 use.

The preview records `mutation_performed=false` and `eligible_for_apply=false`. The D11 mutation gate remains closed: a syntactically valid preview does not establish a supported construction, interoperable peers, adequate tests, or operator authorization.

## Preconditions

The candidate is accepted only when all of these hold:

1. the target is an existing, regular, non-symlink UTF-8 `.py` file no larger than 1 MiB;
2. the path is not generated or vendored;
3. the caller supplies the exact current SHA-256 digest and a positive source line;
4. the module parses successfully;
5. an exact `import hashlib` exists and the `hashlib` name is not reassigned or used as a function parameter;
6. exactly one direct `hashlib.md5(...)` call occurs on the selected line; and
7. the AST byte span contains exactly `hashlib.md5` before diff generation.

Aliases, shadowing, dynamic dispatch, malformed input, stale hashes, unsupported files, ambiguous selections, and generated/vendor paths fail closed.

## Use

```bash
sha256sum sample.py
python3 cli.py preview sample.py \
  --expected-sha256 <64-hex-digest> \
  --line <line-number> \
  --output review-artifacts/latest/d12-preview.json \
  --diff-output review-artifacts/latest/d12-preview.diff
```

Review the JSON and diff. Do not apply the diff without the later D13 isolation and verification controls plus explicit authorization.

## Compatibility warning

MD5 produces a 128-bit digest and SHA-256 produces a 256-bit digest. The preview can therefore break database fields, file formats, protocol fields, signatures, stored values, peers, tests, and APIs. D12 deliberately reports interoperability as unverified.

## Validation

`tests/test_d12_preview.py` covers exact selection, non-mutation, strings/comments, stale hashes, parse failure, aliases, shadowing, multiple candidates, generated paths, and CLI artifact generation. `scripts/run_d12_preview.sh` regenerates deterministic review evidence from a dedicated fixture and confirms the fixture hash is unchanged.
