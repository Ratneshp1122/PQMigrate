"""Role-aware migration planning backed by the D7 YAML knowledge base."""

from __future__ import annotations

from pqc_migration_tool.knowledge.loader import KnowledgeBase, load_default_knowledge_base
from pqc_migration_tool.schema.models import (
    AssuranceRecord,
    ConfidenceLevel,
    CryptoIR,
    MigrationPlan,
)


class MigrationPlanner:
    """Generate advisory plans and enforce ADR-001 abstention."""

    def __init__(self, knowledge_base: KnowledgeBase | None = None) -> None:
        self.knowledge_base = knowledge_base or load_default_knowledge_base()

    @property
    def rules_version(self) -> str:
        return self.knowledge_base.rules_version

    def generate_plan(self, ir: CryptoIR) -> AssuranceRecord:
        if ir.confidence == ConfidenceLevel.AMBIGUOUS:
            return AssuranceRecord(
                finding=ir,
                plan=MigrationPlan(
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
                ),
            )

        rule = self.knowledge_base.match(ir)
        if rule is None:
            return AssuranceRecord(
                finding=ir,
                plan=MigrationPlan(
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
                ),
            )

        return AssuranceRecord(
            finding=ir,
            plan=MigrationPlan(
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
            ),
        )
