"""Generate reproducible evidence for the D11 patch-gate invariant."""

import argparse
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

from .policy import POLICY_VERSION, PatchGate, TriState, evaluate_gate


def build_audit() -> dict:
    evaluated = 0
    eligible_vectors: list[dict[str, str]] = []
    for values in itertools.product(TriState, repeat=5):
        evaluated += 1
        gate = PatchGate(*values)
        if evaluate_gate(gate).eligible:
            eligible_vectors.append(gate.to_dict())
    return {
        "policy_version": POLICY_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_values": [state.value for state in TriState],
        "condition_count": 5,
        "evaluated_combinations": evaluated,
        "eligible_count": len(eligible_vectors),
        "ineligible_count": evaluated - len(eligible_vectors),
        "eligible_vectors": eligible_vectors,
        "invariant": "eligible iff every condition is true",
        "current_pipeline_mutation_enabled": False,
        "report_supplied_eligibility_is_trusted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(build_audit(), indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"D11 patch-policy audit saved → {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
