"""Role-aware planning with D8 decision provenance and priority axes."""

from __future__ import annotations

import hashlib
import json

from pqc_migration_tool.knowledge.loader import KnowledgeBase, load_default_knowledge_base
from pqc_migration_tool.schema.models import (
    AssuranceRecord,
    ConfidenceLevel,
    CryptoIR,
    CryptoOperation,
    CryptoRole,
    DecisionOutcome,
    DecisionTrace,
    DecisionTraceStep,
    MigrationPlan,
    PriorityAssessment,
    PriorityBand,
    ProtocolContext,
    SecurityStatus,
)


class MigrationPlanner:
    """Generate advisory plans and enforce ADR-001 abstention."""

    def __init__(self, knowledge_base: KnowledgeBase | None = None) -> None:
        self.knowledge_base = knowledge_base or load_default_knowledge_base()

    @property
    def rules_version(self) -> str:
        return self.knowledge_base.rules_version

    def generate_plan(self, ir: CryptoIR, source_commit: str | None = None) -> AssuranceRecord:
        if ir.confidence == ConfidenceLevel.AMBIGUOUS:
            plan = MigrationPlan(
                target_algorithm="UNKNOWN",
                target_standard="N/A",
                patch_available=False,
                requires_manual_intervention=True,
                intervention_reason="Role inference failed; cannot safely plan an ambiguous primitive usage.",
                estimated_effort="high",
                rule_id="ABSTAIN-AMBIGUOUS",
                rule_version=self.rules_version,
                blocker_codes=["ROLE_UNKNOWN"],
                standard_refs=[],
            )
            return self._record(
                ir, plan, DecisionOutcome.ABSTAIN,
                match_result="skipped_ambiguous", source_commit=source_commit,
            )

        rule = self.knowledge_base.match(ir)
        if rule is None:
            plan = MigrationPlan(
                target_algorithm="Manual Review",
                target_standard="N/A",
                patch_available=False,
                requires_manual_intervention=True,
                intervention_reason=(
                    f"No enabled knowledge-base rule matches {ir.primitive_name} "
                    f"acting as {ir.role.value}."
                ),
                estimated_effort="high",
                rule_id="ABSTAIN-NO-RULE",
                rule_version=self.rules_version,
                blocker_codes=["NO_MATCHING_RULE"],
                standard_refs=[],
            )
            return self._record(
                ir, plan, DecisionOutcome.ABSTAIN,
                match_result="no_match", source_commit=source_commit,
            )

        plan = MigrationPlan(
            target_algorithm=rule.target_algorithm,
            target_standard=rule.target_standard,
            patch_available=rule.patch_available,
            requires_manual_intervention=rule.requires_manual_intervention,
            intervention_reason=rule.intervention_reason,
            estimated_effort=rule.estimated_effort,
            rule_id=rule.rule_id,
            rule_version=self.rules_version,
            blocker_codes=list(rule.blocker_codes),
            standard_refs=list(rule.standard_refs),
        )
        return self._record(
            ir, plan, DecisionOutcome.RECOMMEND,
            match_result="matched", source_commit=source_commit,
        )

    def _record(
        self,
        ir: CryptoIR,
        plan: MigrationPlan,
        outcome: DecisionOutcome,
        *,
        match_result: str,
        source_commit: str | None,
    ) -> AssuranceRecord:
        plan.priority = self._priority(ir, plan, outcome)
        plan.decision_trace = self._trace(ir, plan, outcome, match_result, source_commit)
        return AssuranceRecord(finding=ir, plan=plan)

    @staticmethod
    def _priority(
        ir: CryptoIR,
        plan: MigrationPlan,
        outcome: DecisionOutcome,
    ) -> PriorityAssessment:
        urgency_by_status = {
            SecurityStatus.QUANTUM_VULNERABLE: PriorityBand.HIGH,
            SecurityStatus.DEPRECATED_CLASSICALLY: PriorityBand.HIGH,
            SecurityStatus.QUANTUM_SECURITY_REDUCED: PriorityBand.MEDIUM,
            SecurityStatus.CONTEXT_DEPENDENT: PriorityBand.MEDIUM,
            SecurityStatus.STANDARDIZED_PQC: PriorityBand.LOW,
            SecurityStatus.UNKNOWN: PriorityBand.UNKNOWN,
        }
        urgency = urgency_by_status[ir.status]
        if outcome == DecisionOutcome.ABSTAIN or urgency == PriorityBand.UNKNOWN:
            overall = PriorityBand.MANUAL_REVIEW
        elif urgency == PriorityBand.HIGH:
            overall = PriorityBand.HIGH
        elif urgency == PriorityBand.MEDIUM:
            overall = PriorityBand.MEDIUM
        else:
            overall = PriorityBand.LOW
        return PriorityAssessment(
            cryptographic_urgency=urgency,
            evidence_strength=ir.confidence,
            migration_effort=plan.estimated_effort,
            data_exposure=PriorityBand.UNKNOWN,
            overall_review_priority=overall,
            basis=[
                f"status={ir.status.value}",
                f"confidence={ir.confidence.value}",
                f"decision={outcome.value}",
                "data_exposure=unknown (not inferred from source)",
            ],
        )

    def _trace(
        self,
        ir: CryptoIR,
        plan: MigrationPlan,
        outcome: DecisionOutcome,
        match_result: str,
        source_commit: str | None,
    ) -> DecisionTrace:
        unresolved = []
        if ir.role == CryptoRole.UNKNOWN:
            unresolved.append("role")
        if ir.operation == CryptoOperation.UNKNOWN:
            unresolved.append("operation")
        if ir.protocol_context == ProtocolContext.UNKNOWN:
            unresolved.append("protocol_context")
        if match_result == "no_match":
            unresolved.append("matching_rule")

        source_ref = {
            "file_path": ir.location.file_path,
            "line_number": ir.location.line_number,
            "column": ir.location.column,
            "source_commit": source_commit,
        }
        steps = [
            DecisionTraceStep(
                stage="detection",
                result="observed",
                explanation="Scanner emitted a typed cryptographic observation without executing target code.",
                facts={
                    "primitive": ir.primitive_name,
                    "detection_type": ir.detection_type,
                    "source_ref": source_ref,
                },
            ),
            DecisionTraceStep(
                stage="role_inference",
                result="unresolved" if ir.confidence == ConfidenceLevel.AMBIGUOUS else "resolved",
                explanation=ir.context_evidence or "Role and operation are taken from the typed finding evidence.",
                facts={
                    "role": ir.role.value,
                    "operation": ir.operation.value,
                    "protocol_context": ir.protocol_context.value,
                    "confidence": ir.confidence.value,
                },
            ),
            DecisionTraceStep(
                stage="rule_match",
                result=match_result,
                explanation=(
                    "The versioned knowledge base selected the recorded rule."
                    if match_result == "matched"
                    else "No recommendation rule was selected; the planner followed an abstention path."
                ),
                facts={"rule_id": plan.rule_id, "rules_version": self.rules_version},
            ),
            DecisionTraceStep(
                stage="blocker_assessment",
                result="blocked" if plan.blocker_codes else "clear",
                explanation="Blockers are explicit prerequisites for any future migration action.",
                facts={"blocker_codes": list(plan.blocker_codes)},
            ),
            DecisionTraceStep(
                stage="decision",
                result=outcome.value,
                explanation=plan.intervention_reason or "Advisory recommendation generated.",
                facts={
                    "target_algorithm": plan.target_algorithm,
                    "target_standard": plan.target_standard,
                    "patch_available": plan.patch_available,
                    "requires_manual_intervention": plan.requires_manual_intervention,
                },
            ),
        ]
        canonical = {
            "finding": {
                "id": ir.id,
                "primitive": ir.primitive_name,
                "source_ref": source_ref,
                "role": ir.role.value,
                "operation": ir.operation.value,
                "status": ir.status.value,
                "confidence": ir.confidence.value,
                "protocol_context": ir.protocol_context.value,
            },
            "decision": {
                "outcome": outcome.value,
                "rule_id": plan.rule_id,
                "rules_version": self.rules_version,
                "blocker_codes": plan.blocker_codes,
                "target_algorithm": plan.target_algorithm,
            },
        }
        trace_id = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:16]
        return DecisionTrace(
            trace_id=trace_id,
            finding_id=ir.id,
            outcome=outcome,
            source_ref=source_ref,
            steps=steps,
            unresolved_fields=unresolved,
        )
