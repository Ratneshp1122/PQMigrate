"""Strict loader for the D7 YAML migration knowledge base."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from pqc_migration_tool.schema.models import CryptoIR, CryptoRole, ProtocolContext, SecurityStatus


class KnowledgeBaseError(ValueError):
    """Raised when the knowledge base is missing or invalid."""


@dataclass(frozen=True)
class KnowledgeRule:
    rule_id: str
    priority: int
    primitive_contains: tuple[str, ...]
    roles: tuple[CryptoRole, ...]
    statuses: tuple[SecurityStatus, ...]
    protocol_contexts: tuple[ProtocolContext, ...]
    target_algorithm: str
    target_standard: str
    patch_available: bool
    requires_manual_intervention: bool
    intervention_reason: str
    estimated_effort: str
    blocker_codes: tuple[str, ...]
    standard_refs: tuple[str, ...]

    def matches(self, finding: CryptoIR) -> bool:
        primitive = finding.primitive_name.casefold()
        if not any(fragment in primitive for fragment in self.primitive_contains):
            return False
        if finding.role not in self.roles:
            return False
        if finding.status not in self.statuses:
            return False
        if self.protocol_contexts and finding.protocol_context not in self.protocol_contexts:
            return False
        return True


@dataclass(frozen=True)
class KnowledgeBase:
    schema_version: int
    rules_version: str
    rules: tuple[KnowledgeRule, ...]
    source_path: Path

    def match(self, finding: CryptoIR) -> KnowledgeRule | None:
        return next((rule for rule in self.rules if rule.matches(finding)), None)

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeBase":
        source_path = Path(path).resolve()
        try:
            raw = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise KnowledgeBaseError(f"Cannot read knowledge base {source_path}: {exc}") from exc
        except yaml.YAMLError as exc:
            raise KnowledgeBaseError(f"Invalid YAML in {source_path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise KnowledgeBaseError("Knowledge base root must be a mapping.")
        if raw.get("schema_version") != 1:
            raise KnowledgeBaseError("schema_version must be 1.")
        rules_version = raw.get("rules_version")
        if not isinstance(rules_version, str) or not rules_version.strip():
            raise KnowledgeBaseError("rules_version must be a non-empty string.")
        raw_rules = raw.get("rules")
        if not isinstance(raw_rules, list) or not raw_rules:
            raise KnowledgeBaseError("rules must be a non-empty list.")

        seen_ids: set[str] = set()
        rules = [cls._parse_rule(item, index, seen_ids) for index, item in enumerate(raw_rules)]
        rules.sort(key=lambda rule: (-rule.priority, rule.rule_id))
        return cls(1, rules_version, tuple(rules), source_path)

    @staticmethod
    def _string_list(value: Any, field_name: str, *, required: bool = True) -> tuple[str, ...]:
        if value is None and not required:
            return ()
        if not isinstance(value, list) or (required and not value):
            raise KnowledgeBaseError(f"{field_name} must be a non-empty list.")
        if not all(isinstance(item, str) and item.strip() for item in value):
            raise KnowledgeBaseError(f"{field_name} must contain non-empty strings.")
        return tuple(item.strip() for item in value)

    @classmethod
    def _parse_rule(cls, raw: Any, index: int, seen_ids: set[str]) -> KnowledgeRule:
        label = f"rules[{index}]"
        if not isinstance(raw, dict):
            raise KnowledgeBaseError(f"{label} must be a mapping.")
        rule_id = raw.get("id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise KnowledgeBaseError(f"{label}.id must be a non-empty string.")
        if rule_id in seen_ids:
            raise KnowledgeBaseError(f"Duplicate rule id: {rule_id}.")
        seen_ids.add(rule_id)

        priority = raw.get("priority")
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise KnowledgeBaseError(f"{rule_id}.priority must be an integer.")
        match = raw.get("match")
        plan = raw.get("plan")
        if not isinstance(match, dict) or not isinstance(plan, dict):
            raise KnowledgeBaseError(f"{rule_id} requires match and plan mappings.")

        fragments = tuple(
            fragment.casefold()
            for fragment in cls._string_list(match.get("primitive_contains"), f"{rule_id}.match.primitive_contains")
        )
        role_names = cls._string_list(match.get("roles"), f"{rule_id}.match.roles")
        try:
            roles = tuple(CryptoRole(name) for name in role_names)
        except ValueError as exc:
            raise KnowledgeBaseError(f"{rule_id}.match.roles contains an unsupported role: {exc}") from exc

        status_names = cls._string_list(match.get("statuses"), f"{rule_id}.match.statuses")
        try:
            statuses = tuple(SecurityStatus(name) for name in status_names)
        except ValueError as exc:
            raise KnowledgeBaseError(f"{rule_id}.match.statuses contains an unsupported status: {exc}") from exc

        context_names = cls._string_list(
            match.get("protocol_contexts"),
            f"{rule_id}.match.protocol_contexts",
            required=False,
        )
        try:
            contexts = tuple(ProtocolContext(name) for name in context_names)
        except ValueError as exc:
            raise KnowledgeBaseError(
                f"{rule_id}.match.protocol_contexts contains an unsupported context: {exc}"
            ) from exc

        required_plan_strings = (
            "target_algorithm",
            "target_standard",
            "intervention_reason",
            "estimated_effort",
        )
        for field_name in required_plan_strings:
            if not isinstance(plan.get(field_name), str) or not plan[field_name].strip():
                raise KnowledgeBaseError(f"{rule_id}.plan.{field_name} must be a non-empty string.")
        if plan.get("patch_available") is not False:
            raise KnowledgeBaseError(f"{rule_id}.plan.patch_available must be false in D7.")
        if plan.get("requires_manual_intervention") is not True:
            raise KnowledgeBaseError(f"{rule_id}.plan.requires_manual_intervention must be true in D7.")

        blockers = cls._string_list(plan.get("blocker_codes"), f"{rule_id}.plan.blocker_codes")
        refs = cls._string_list(plan.get("standard_refs"), f"{rule_id}.plan.standard_refs")
        return KnowledgeRule(
            rule_id=rule_id,
            priority=priority,
            primitive_contains=fragments,
            roles=roles,
            statuses=statuses,
            protocol_contexts=contexts,
            target_algorithm=plan["target_algorithm"].strip(),
            target_standard=plan["target_standard"].strip(),
            patch_available=False,
            requires_manual_intervention=True,
            intervention_reason=plan["intervention_reason"].strip(),
            estimated_effort=plan["estimated_effort"].strip(),
            blocker_codes=blockers,
            standard_refs=refs,
        )


DEFAULT_KNOWLEDGE_PATH = Path(__file__).with_name("migration_rules.yaml")


def load_default_knowledge_base() -> KnowledgeBase:
    configured_path = os.environ.get("PQMIGRATE_KNOWLEDGE_PATH")
    return KnowledgeBase.load(configured_path or DEFAULT_KNOWLEDGE_PATH)
