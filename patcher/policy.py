"""D11 fail-closed policy gate for any future source mutation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


POLICY_VERSION = "2026.09.27-d11.1"


class TriState(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PatchGate:
    """The five independent conditions required by the review safety model."""

    known_role: TriState = TriState.UNKNOWN
    supported_construction: TriState = TriState.UNKNOWN
    interoperable_peers: TriState = TriState.UNKNOWN
    tests_available: TriState = TriState.UNKNOWN
    operator_authorized: TriState = TriState.UNKNOWN

    def to_dict(self) -> dict[str, str]:
        return {name: value.value for name, value in self.__dict__.items()}


@dataclass(frozen=True)
class PatchPolicyDecision:
    eligible: bool
    gate: PatchGate
    blocker_codes: tuple[str, ...] = field(default_factory=tuple)
    policy_version: str = POLICY_VERSION
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "policy_version": self.policy_version,
            "conditions": self.gate.to_dict(),
            "blocker_codes": list(self.blocker_codes),
            "explanation": self.explanation,
        }


def evaluate_gate(gate: PatchGate) -> PatchPolicyDecision:
    """Apply strong Kleene-style conjunction: only five TRUE values are eligible."""
    blockers = tuple(
        f"PATCH_{name.upper()}_{value.value.upper()}"
        for name, value in gate.__dict__.items()
        if value is not TriState.TRUE
    )
    eligible = not blockers
    explanation = (
        "All five independently evidenced conditions are true."
        if eligible
        else "Automatic mutation refused because at least one required condition is false or unknown."
    )
    return PatchPolicyDecision(
        eligible=eligible,
        gate=gate,
        blocker_codes=blockers,
        explanation=explanation,
    )


def assess_record(record: dict[str, Any]) -> PatchPolicyDecision:
    """Assess current report evidence without trusting self-asserted eligibility fields.

    D11 can establish a known role from the typed finding. The current pipeline does
    not independently establish a supported rewrite, peer interoperability, an
    isolated test contract, or operator authorization. Those conditions therefore
    remain UNKNOWN and make every current report ineligible for mutation.
    """
    finding = record.get("finding") or {}
    role = finding.get("role")
    known_role = TriState.TRUE if role and role != "unknown" else TriState.UNKNOWN
    return evaluate_gate(PatchGate(known_role=known_role))
