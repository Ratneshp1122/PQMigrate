# PQMigrate algorithm and mathematical model

## Review claim

PQMigrate separates primitive discovery from semantic role inference. A source import can establish an inventory lead, but only a linked operation can establish `SIGNATURE`, `KEY_TRANSPORT`, or another role. When the evidence is missing or conflicting, the system returns `UNKNOWN` and the planner abstains from automatic mutation.

## Current bounded algorithm

```text
SCAN(source tree, rule registry):
  enumerate supported source files without executing them
  parse each Python file into an AST
  discover Go inventory leads with bounded patterns
  parse Go RSA candidates with the Tree-sitter Go grammar
  emit primitive inventory leads and supported direct call findings
  for each RSA lead:
    partition observations by module or function scope
    record variables assigned by supported RSA key-generation calls
    record variables assigned or filled by supported secure-random calls
    link a tracked RSA key to a later operation in the same scope
    if jwt.encode consumes that exact key with an RS* algorithm:
      return SIGNATURE, JWT, and the call-line evidence
    if RSA encrypt consumes a tracked generated session secret:
      return KEY_TRANSPORT and both evidence lines
    if linked RSA roles conflict:
      return UNKNOWN with the conflicting evidence
    if no linked use exists:
      return UNKNOWN as an inventory lead
  create a role-aware advisory plan
  keep patch_available=false until separate eligibility checks pass
```

## Formal role function

For observation `x`, let `E(x)` contain resolved imports, AST spans, same-scope assignments, and linked calls.

```text
rho(x) = SIGNATURE
  when a resolved signing operation consumes the tracked key

rho(x) = KEY_TRANSPORT
  when RSA encrypt consumes a tracked locally generated session secret

rho(x) = UNKNOWN
  when neither condition holds or observed roles conflict
```

The current implementation proves corresponding bounded Python and Go cases:

- `jwt.encode(payload, signing_key, algorithm="RS256")` is a signature only when `signing_key` is the tracked generated RSA key.
- RSA encryption is key transport only when the encrypted argument is a tracked session secret produced by a supported secure-random call.

Same-function proximity alone does not satisfy either rule.

## Conservative migration eligibility

```text
AutoEligible(x) =
  KnownRole(x)
  AND SupportedConstruction(x)
  AND InteroperablePeers(x)
  AND RequiredTestsPass(x)
  AND OperatorAuthorized(x)
```

The conjunction uses three-valued logic. `unknown` prevents automatic mutation. The current scanner does not establish all five conditions, so the planner always emits `patch_available=false` for RSA signature and key-transport advice.

## Complexity

Let `N_py` and `N_go` be parsed Python and Go syntax nodes, `F` emitted findings, `D` bounded dataflow links, `P` regex patterns, and `B_go` Go source bytes.

- Python parsing and traversal: approximately `O(N_py)`.
- Go inventory discovery: approximately `O(P × B_go)` for ordinary bounded patterns.
- Tree-sitter Go parsing and bounded traversal: approximately `O(N_go)` under ordinary parser behavior.
- Bounded role inference: `O(N_py + N_go + D)` across parsed candidates with indexed variable sets.
- Report construction: `O(F)` beyond parsing and inference.
- In-memory syntax analysis: `O(N_py + N_go + F + D)`.

## Verified review cases

| Fixture | Proven result | Plan |
|---|---|---|
| RSA JWT signing | `SIGNATURE`, `JWT`, direct evidence at `jwt.encode` | ML-DSA assessment, manual intervention |
| RSA generated-session-key encryption | `KEY_TRANSPORT`, direct evidence linking generation and encryption | ML-KEM-based KEM/DEM redesign, manual intervention |
| RSA import only | `UNKNOWN`, ambiguous inventory lead | `UNKNOWN`, abstain |
| JWT call with an unrelated key | `UNKNOWN` | abstain |
| One RSA key used for conflicting roles | `UNKNOWN` with conflict trace | abstain |

These fixtures demonstrate bounded behavior, not general accuracy. D9 adds a 72-case single-author synthetic pilot with 68 evaluated cases and four separately counted parse failures. Its raw predictions and metrics are reproducible, but publication-quality accuracy still requires independently labelled real-project cases.
