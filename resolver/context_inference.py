"""Bounded Python role and protocol inference for reviewable RSA cases.

The analyzer never imports or executes target code. It links operations only
inside one module/function scope and abstains when evidence conflicts.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from pqc_migration_tool.schema.models import (
    ConfidenceLevel,
    CryptoOperation,
    CryptoRole,
    ProtocolContext,
)


@dataclass(frozen=True)
class InferenceResult:
    role: CryptoRole = CryptoRole.UNKNOWN
    operation: CryptoOperation = CryptoOperation.UNKNOWN
    protocol_context: ProtocolContext = ProtocolContext.UNKNOWN
    confidence: ConfidenceLevel = ConfidenceLevel.AMBIGUOUS
    evidence: str = "No linked RSA operation was found."
    evidence_line: int | None = None


class _ScopeCollector(ast.NodeVisitor):
    """Collect nodes without descending into nested functions or classes."""

    def __init__(self) -> None:
        self.nodes: list[ast.AST] = []

    def generic_visit(self, node: ast.AST) -> None:
        self.nodes.append(node)
        super().generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return


def _nodes_in_scope(statements: list[ast.stmt]) -> list[ast.AST]:
    collector = _ScopeCollector()
    for statement in statements:
        collector.visit(statement)
    return collector.nodes


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _root_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _root_name(node.value)
    if isinstance(node, ast.Call):
        return _root_name(node.func)
    return None


class PythonRoleAnalyzer:
    """Infer a small set of RSA roles using same-scope dataflow."""

    def __init__(self, source_code: str, filename: str = "<unknown>") -> None:
        self.tree = ast.parse(source_code, filename=filename)
        self.module_imports = self._collect_imports(_nodes_in_scope(self.tree.body))

    @staticmethod
    def _collect_imports(nodes: list[ast.AST]) -> dict[str, str]:
        imports: dict[str, str] = {}
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.asname or alias.name.split(".")[0]] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports[alias.asname or alias.name] = f"{module}.{alias.name}"
        return imports

    @staticmethod
    def _resolved_call_name(call: ast.Call, imports: dict[str, str]) -> str:
        dotted = _dotted_name(call.func)
        if not dotted:
            return ""
        first, *rest = dotted.split(".")
        resolved = imports.get(first, first)
        return ".".join([resolved, *rest]) if rest else resolved

    @staticmethod
    def _assigned_name(node: ast.Assign | ast.AnnAssign) -> str | None:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if len(targets) == 1 and isinstance(targets[0], ast.Name):
            return targets[0].id
        return None

    @staticmethod
    def _literal_string(node: ast.AST | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _analyze_scope(self, statements: list[ast.stmt]) -> list[InferenceResult]:
        nodes = _nodes_in_scope(statements)
        imports = dict(self.module_imports)
        imports.update(self._collect_imports(nodes))
        rsa_keys: dict[str, int] = {}
        session_secrets: dict[str, int] = {}

        for node in sorted(nodes, key=lambda item: getattr(item, "lineno", 0)):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            assigned = self._assigned_name(node)
            if assigned is None or not isinstance(value, ast.Call):
                continue
            call_name = self._resolved_call_name(value, imports)
            if call_name.endswith(".rsa.generate_private_key"):
                rsa_keys[assigned] = node.lineno
            elif call_name in {"os.urandom", "secrets.token_bytes", "secrets.token_hex"}:
                session_secrets[assigned] = node.lineno

        results: list[InferenceResult] = []
        for node in sorted(nodes, key=lambda item: getattr(item, "lineno", 0)):
            if not isinstance(node, ast.Call):
                continue
            call_name = self._resolved_call_name(node, imports)

            if call_name == "jwt.encode" and len(node.args) >= 2:
                key_name = node.args[1].id if isinstance(node.args[1], ast.Name) else None
                algorithm = next(
                    (self._literal_string(keyword.value) for keyword in node.keywords if keyword.arg == "algorithm"),
                    None,
                )
                if (
                    key_name in rsa_keys
                    and rsa_keys[key_name] < node.lineno
                    and algorithm is not None
                    and algorithm.upper().startswith("RS")
                ):
                    results.append(InferenceResult(
                        role=CryptoRole.SIGNATURE,
                        operation=CryptoOperation.SIGN,
                        protocol_context=ProtocolContext.JWT,
                        confidence=ConfidenceLevel.DIRECT,
                        evidence=f"Line {node.lineno}: jwt.encode consumes tracked RSA key '{key_name}' with algorithm '{algorithm}'.",
                        evidence_line=node.lineno,
                    ))
                continue

            if not isinstance(node.func, ast.Attribute):
                continue
            method = node.func.attr
            key_name = _root_name(node.func.value)
            if key_name not in rsa_keys or rsa_keys[key_name] >= node.lineno:
                continue

            if method in {"sign", "verify"}:
                operation = CryptoOperation.SIGN if method == "sign" else CryptoOperation.VERIFY
                results.append(InferenceResult(
                    role=CryptoRole.SIGNATURE,
                    operation=operation,
                    confidence=ConfidenceLevel.DIRECT,
                    evidence=f"Line {node.lineno}: RSA key '{key_name}' is used by .{method}().",
                    evidence_line=node.lineno,
                ))
            elif method == "encrypt":
                plaintext = node.args[0].id if node.args and isinstance(node.args[0], ast.Name) else None
                if plaintext in session_secrets and session_secrets[plaintext] < node.lineno:
                    results.append(InferenceResult(
                        role=CryptoRole.KEY_TRANSPORT,
                        operation=CryptoOperation.ENCRYPT,
                        confidence=ConfidenceLevel.DIRECT,
                        evidence=(
                            f"Line {node.lineno}: RSA key '{key_name}' encrypts tracked session secret "
                            f"'{plaintext}' generated on line {session_secrets[plaintext]}."
                        ),
                        evidence_line=node.lineno,
                    ))
                else:
                    results.append(InferenceResult(
                        role=CryptoRole.ENCRYPTION,
                        operation=CryptoOperation.ENCRYPT,
                        confidence=ConfidenceLevel.INFERRED,
                        evidence=f"Line {node.lineno}: RSA key '{key_name}' encrypts data whose session-key purpose is unresolved.",
                        evidence_line=node.lineno,
                    ))
            elif method == "decrypt":
                results.append(InferenceResult(
                    role=CryptoRole.ENCRYPTION,
                    operation=CryptoOperation.DECRYPT,
                    confidence=ConfidenceLevel.INFERRED,
                    evidence=f"Line {node.lineno}: RSA key '{key_name}' decrypts data; transport purpose is unresolved.",
                    evidence_line=node.lineno,
                ))

        return results

    def infer_rsa_usage(self) -> InferenceResult:
        results = self._analyze_scope(self.tree.body)
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                results.extend(self._analyze_scope(node.body))

        if not results:
            return InferenceResult()

        distinct_roles = {result.role for result in results}
        if len(distinct_roles) != 1:
            evidence = "Conflicting RSA roles observed: " + "; ".join(result.evidence for result in results)
            return InferenceResult(evidence=evidence)

        return min(results, key=lambda result: result.evidence_line or 0)


def infer_rsa_usage(source_code: str, filename: str = "<unknown>") -> InferenceResult:
    try:
        return PythonRoleAnalyzer(source_code, filename).infer_rsa_usage()
    except SyntaxError as exc:
        return InferenceResult(evidence=f"AST parsing failed: {exc.msg} at line {exc.lineno}.")
