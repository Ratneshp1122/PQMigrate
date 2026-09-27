from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from pqc_migration_tool.knowledge.loader import (
    DEFAULT_KNOWLEDGE_PATH,
    KnowledgeBase,
    KnowledgeBaseError,
    load_default_knowledge_base,
)
from pqc_migration_tool.resolver.planner import MigrationPlanner
from pqc_migration_tool.schema.models import (
    CodeLocation,
    ConfidenceLevel,
    CryptoIR,
    CryptoOperation,
    CryptoRole,
    SecurityStatus,
)


def _finding(role: CryptoRole, primitive: str = "RSA") -> CryptoIR:
    return CryptoIR(
        id="fixture",
        primitive_name=primitive,
        location=CodeLocation(file_path="fixture.py", line_number=1),
        role=role,
        operation=CryptoOperation.SIGN if role == CryptoRole.SIGNATURE else CryptoOperation.ENCRYPT,
        status=SecurityStatus.QUANTUM_VULNERABLE,
        confidence=ConfidenceLevel.DIRECT,
        detection_type="linked_operation",
    )


def _raw_default() -> dict:
    return yaml.safe_load(DEFAULT_KNOWLEDGE_PATH.read_text(encoding="utf-8"))


def test_default_knowledge_base_is_versioned_and_unique() -> None:
    knowledge = load_default_knowledge_base()

    assert knowledge.schema_version == 1
    assert knowledge.rules_version == "2026.09.26-d7.1"
    assert len(knowledge.rules) == 9
    assert len({rule.rule_id for rule in knowledge.rules}) == len(knowledge.rules)


def test_planner_uses_role_specific_yaml_rule_metadata() -> None:
    record = MigrationPlanner().generate_plan(_finding(CryptoRole.SIGNATURE))

    assert record.plan is not None
    assert record.plan.rule_id == "RSA-SIGNATURE-001"
    assert record.plan.rule_version == "2026.09.26-d7.1"
    assert record.plan.target_standard == "FIPS 204"
    assert "VERIFIER_SUPPORT" in record.plan.blocker_codes
    assert record.plan.standard_refs
    assert record.plan.patch_available is False
    assert record.plan.decision_trace is not None
    assert record.plan.decision_trace.outcome.value == "recommend"
    assert [step.stage for step in record.plan.decision_trace.steps] == [
        "detection",
        "role_inference",
        "rule_match",
        "blocker_assessment",
        "decision",
    ]
    assert record.plan.priority is not None
    assert record.plan.priority.cryptographic_urgency.value == "high"
    assert record.plan.priority.overall_review_priority.value == "high"
    assert record.plan.priority.data_exposure.value == "unknown"


def test_ambiguous_finding_abstains_before_rule_matching() -> None:
    finding = _finding(CryptoRole.UNKNOWN)
    finding.confidence = ConfidenceLevel.AMBIGUOUS

    record = MigrationPlanner().generate_plan(finding)

    assert record.plan is not None
    assert record.plan.rule_id == "ABSTAIN-AMBIGUOUS"
    assert record.plan.blocker_codes == ["ROLE_UNKNOWN"]
    assert record.plan.decision_trace is not None
    assert record.plan.decision_trace.outcome.value == "abstain"
    assert "role" in record.plan.decision_trace.unresolved_fields
    assert record.plan.priority is not None
    assert record.plan.priority.overall_review_priority.value == "manual_review"


def test_decision_trace_id_is_deterministic_for_equivalent_input() -> None:
    planner = MigrationPlanner()

    first = planner.generate_plan(_finding(CryptoRole.SIGNATURE))
    second = planner.generate_plan(_finding(CryptoRole.SIGNATURE))

    assert first.plan is not None and first.plan.decision_trace is not None
    assert second.plan is not None and second.plan.decision_trace is not None
    assert first.plan.decision_trace.trace_id == second.plan.decision_trace.trace_id


def test_trace_id_changes_when_semantic_decision_input_changes() -> None:
    planner = MigrationPlanner()
    signature = planner.generate_plan(_finding(CryptoRole.SIGNATURE))
    transport = planner.generate_plan(_finding(CryptoRole.KEY_TRANSPORT))

    assert signature.plan is not None and signature.plan.decision_trace is not None
    assert transport.plan is not None and transport.plan.decision_trace is not None
    assert signature.plan.decision_trace.trace_id != transport.plan.decision_trace.trace_id


def test_duplicate_rule_ids_are_rejected(tmp_path: Path) -> None:
    raw = _raw_default()
    raw["rules"].append(deepcopy(raw["rules"][0]))
    path = tmp_path / "duplicate.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")

    with pytest.raises(KnowledgeBaseError, match="Duplicate rule id"):
        KnowledgeBase.load(path)


def test_d7_rule_cannot_enable_automatic_patch(tmp_path: Path) -> None:
    raw = _raw_default()
    raw["rules"][0]["plan"]["patch_available"] = True
    path = tmp_path / "unsafe.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")

    with pytest.raises(KnowledgeBaseError, match="patch_available must be false"):
        KnowledgeBase.load(path)


def test_unknown_role_name_is_rejected(tmp_path: Path) -> None:
    raw = _raw_default()
    raw["rules"][0]["match"]["roles"] = ["made_up_role"]
    path = tmp_path / "bad-role.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")

    with pytest.raises(KnowledgeBaseError, match="unsupported role"):
        KnowledgeBase.load(path)


def test_classical_signature_rule_does_not_match_standardized_ml_dsa() -> None:
    finding = _finding(CryptoRole.SIGNATURE, primitive="ML-DSA-65 (FIPS 204)")
    finding.status = SecurityStatus.STANDARDIZED_PQC

    record = MigrationPlanner().generate_plan(finding)

    assert record.plan is not None
    assert record.plan.rule_id == "ABSTAIN-NO-RULE"
    assert record.plan.target_algorithm == "Manual Review"
    assert record.plan.decision_trace is not None
    assert "matching_rule" in record.plan.decision_trace.unresolved_fields


def test_environment_can_select_an_alternate_valid_rule_file(tmp_path: Path, monkeypatch) -> None:
    raw = _raw_default()
    raw["rules_version"] = "test-rules"
    path = tmp_path / "alternate.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    monkeypatch.setenv("PQMIGRATE_KNOWLEDGE_PATH", str(path))

    knowledge = load_default_knowledge_base()

    assert knowledge.rules_version == "test-rules"
    assert knowledge.source_path == path.resolve()
