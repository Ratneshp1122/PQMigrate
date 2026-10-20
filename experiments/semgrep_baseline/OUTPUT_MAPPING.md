# Output mapping, version 1 (unscored)

This policy uses the reviewer SOP vocabulary as requested by Ratnesh. Predictions
are not reviewer labels. It does not create or alter A/B submissions, adjudicated
gold, assigned candidate IDs, or reviewer `review_status`.

| Output field | Contract |
|---|---|
| `predicted_presence` | `yes`, `no`, `uncertain`; emitted rules currently use yes/uncertain |
| `predicted_operation` | `sign`, `verify`, `encrypt`, `decrypt`, `key_establish`, `hash`, `mac`, `kdf`, `key_generate`, `other_crypto`, `none`, `uncertain` |
| `predicted_role` | `signature`, `key_transport`, `key_establishment`, `encryption`, `hash`, `mac`, `kdf`, `key_management`, `other`, `none`, `uncertain` |
| `predicted_context` | `unknown`; the baseline does not infer application context |
| `uncertainty_reason` | Required for every unresolved prediction |
| `start`, `end` | Native Semgrep 1-based line/column and byte offsets, end exclusive |
| `rule_id`, `raw_result_index` | Link to exact native finding and committed mapping policy |
| `repository`, `commit`, `path`, `source_sha256` | Frozen source identity, or null repository fields for synthetic snippets |

`mapping.json` is authoritative and hashed in each run. Qualified Python API
syntax predicts key creation as `key_generate`/`key_management`, key loading as
`other_crypto`/`key_management`, hashing as `hash`/`hash`, and MAC construction or
evaluation as `mac`/`mac`. These are static API predictions and can be wrong under
shadowing, monkey patching or imports that resolve to a different implementation.
They do not prove execution in production. Hash/MAC context construction is
included explicitly as a management/setup invocation, rather than asserting that
a digest was computed there. Descriptor-only algorithm construction is excluded.
These scope choices must be reconciled with adjudicated operation units before
scoring; they are not retrospective changes to gold.

Receiver-only methods (including `.sign`, `.digest`, `.finalize`, Go `Sign`,
`Sum`, `Seal`, `Open`) emit `uncertain` in all three fields. Go package-import
patterns also retain `uncertain` because this baseline does not resolve shadowing
or receiver types. A method name does not prove cryptography. Native metadata's
`candidate_operation` is a search hint and is never promoted to an SOP operation.
No flow evidence is used to infer key transport. Exchange/encapsulation names
remain unresolved without provider evidence. Wrappers and unavailable boundaries
are not claimed to be proven calls. The baseline intentionally has limited scope.

An absent finding does not create `no`/`none`/`none`. It is simply no rule match.
`no` requires a separate scored unit with a supported non-crypto interpretation.
Parse failures and unresolved candidates cannot be counted as true negatives.

One normalized record corresponds to one native rule finding. Duplicate,
overlapping and nested spans are retained in order, not arbitrarily merged or
reduced to a single operation. `gold_alignment=pending_operation_unit_decision`
prevents treating these as scored operations. A later, versioned alignment must
use frozen candidate IDs and exact call spans, preserve unmatched findings, apply
the SOP `MULTIPLE:` expansion through adjudication, and document one-to-many
matching, setup calls, streaming stages and failures before computing metrics.
Do not compare file-level finding counts to the paper's snippet-level pilot
metrics. Candidate-selected anchors alone cannot estimate TPR/recall for missed
operations; the independent-search/ordinary-source sample is required.
