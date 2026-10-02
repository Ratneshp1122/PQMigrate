"""Bounded Go RSA role inference backed by a real Go syntax tree.

The resolver parses source with Tree-sitter's Go grammar and performs
same-function, forward-only data-flow tracking.  It deliberately abstains
when a key cannot be linked, an import alias is shadowed, syntax is malformed,
or more than one cryptographic role is observed.

This module never compiles, imports, or executes the target Go source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from pqc_migration_tool.resolver.context_inference import InferenceResult
from pqc_migration_tool.schema.models import (
    ConfidenceLevel,
    CryptoOperation,
    CryptoRole,
)

try:
    from tree_sitter import Language, Node, Parser
    import tree_sitter_go
except ImportError:  # The report path must fail closed when the optional parser is absent.
    Language = Node = Parser = None  # type: ignore[assignment,misc]
    tree_sitter_go = None


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_IMPORT_SPEC = re.compile(
    r'^\s*(?:(?P<alias>[A-Za-z_][A-Za-z0-9_]*|\.)\s+)?"(?P<path>[^"]+)"\s*$'
)
_TYPED_RSA_PARAMETER = re.compile(
    r"\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+\*?(?P<alias>[A-Za-z_][A-Za-z0-9_]*)\.(?P<kind>PrivateKey|PublicKey)\b"
)


@dataclass(frozen=True)
class _Operation:
    result: InferenceResult
    key_name: str


def go_semantic_parser_available() -> bool:
    """Return whether the runtime contains the pinned Go grammar dependency."""

    return Parser is not None and Language is not None and tree_sitter_go is not None


def _text(source: bytes, node: "Node") -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _walk(node: "Node", *, skip_nested_functions: bool = False) -> Iterable["Node"]:
    yield node
    for child in node.named_children:
        if skip_nested_functions and child.type in {
            "function_declaration", "method_declaration", "func_literal"
        }:
            continue
        yield from _walk(child, skip_nested_functions=skip_nested_functions)


def _line(node: "Node") -> int:
    return node.start_point[0] + 1


def _identifier(text: str) -> str | None:
    value = text.strip().lstrip("&*").strip()
    return value if _IDENTIFIER.fullmatch(value) else None


def _root_identifier(text: str) -> str | None:
    value = text.strip().lstrip("&*").strip()
    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", value)
    return match.group(1) if match else None


def _call_parts(source: bytes, call: "Node") -> tuple[str, list[str]]:
    function = call.child_by_field_name("function")
    arguments = call.child_by_field_name("arguments")
    if function is None or arguments is None:
        return "", []
    args = [_text(source, child).strip() for child in arguments.named_children]
    return _text(source, function).strip(), args


def _assignment_parts(source: bytes, node: "Node") -> tuple[list[str], list[str]]:
    left = node.child_by_field_name("left")
    right = node.child_by_field_name("right")
    if left is None or right is None:
        return [], []
    left_values = [
        _text(source, child).strip() for child in left.named_children
    ] or [_text(source, left).strip()]
    right_values = [
        _text(source, child).strip() for child in right.named_children
    ] or [_text(source, right).strip()]
    return left_values, right_values


class GoRoleAnalyzer:
    """Infer bounded RSA roles using Go CST nodes and same-scope data flow."""

    def __init__(self, source_code: str, filename: str = "<unknown>") -> None:
        if not go_semantic_parser_available():
            raise RuntimeError(
                "Go semantic parser unavailable; install tree-sitter and tree-sitter-go."
            )
        self.filename = filename
        self.source = source_code.encode("utf-8")
        language = Language(tree_sitter_go.language())
        self.tree = Parser(language).parse(self.source)

    def _rsa_import_aliases(self) -> set[str]:
        aliases: set[str] = set()
        for node in _walk(self.tree.root_node):
            if node.type != "import_spec":
                continue
            match = _IMPORT_SPEC.match(_text(self.source, node))
            if not match or match.group("path") != "crypto/rsa":
                continue
            alias = match.group("alias") or "rsa"
            if alias not in {"_", "."}:
                aliases.add(alias)
        return aliases

    def _scope_nodes(self, scope: "Node") -> list["Node"]:
        nodes = list(_walk(scope, skip_nested_functions=True))
        return sorted(nodes, key=lambda node: (node.start_byte, node.end_byte))

    def _typed_parameters(
        self, scope: "Node", rsa_aliases: set[str]
    ) -> tuple[dict[str, int], dict[str, int]]:
        private_keys: dict[str, int] = {}
        public_keys: dict[str, int] = {}
        parameters = scope.child_by_field_name("parameters")
        if parameters is None:
            return private_keys, public_keys
        for match in _TYPED_RSA_PARAMETER.finditer(_text(self.source, parameters)):
            if match.group("alias") not in rsa_aliases:
                continue
            target = private_keys if match.group("kind") == "PrivateKey" else public_keys
            target[match.group("name")] = _line(scope)
        return private_keys, public_keys

    @staticmethod
    def _package_call(function: str) -> tuple[str, str] | None:
        if "." not in function:
            return None
        alias, method = function.split(".", 1)
        return alias, method

    def _analyze_scope(self, scope: "Node", rsa_aliases: set[str]) -> list[_Operation]:
        private_keys, public_keys = self._typed_parameters(scope, rsa_aliases)
        byte_buffers: dict[str, int] = {}
        session_secrets: dict[str, int] = {}
        shadowed_aliases: set[str] = set()
        operations: list[_Operation] = []

        nodes = self._scope_nodes(scope)
        for node in nodes:
            line = _line(node)

            if node.type in {"short_var_declaration", "assignment_statement"}:
                left_values, right_values = _assignment_parts(self.source, node)
                left_names = [name for value in left_values if (name := _identifier(value))]
                if node.type == "short_var_declaration":
                    shadowed_aliases.update(set(left_names) & rsa_aliases)

                if not left_names or not right_values:
                    continue
                first_name = left_names[0]
                first_value = right_values[0]

                make_match = re.fullmatch(r"make\s*\(\s*\[\s*\]byte\s*,.*\)", first_value, re.DOTALL)
                if make_match:
                    byte_buffers[first_name] = line

                if re.fullmatch(r"&?\s*[A-Za-z_][A-Za-z0-9_]*\.PublicKey", first_value):
                    base = _root_identifier(first_value)
                    if base in private_keys:
                        public_keys[first_name] = line

                for alias in rsa_aliases - shadowed_aliases:
                    if re.match(rf"^{re.escape(alias)}\.Generate(?:MultiPrime)?Key\s*\(", first_value):
                        private_keys[first_name] = line

            if node.type != "call_expression":
                continue

            function, args = _call_parts(self.source, node)
            if not function:
                continue

            # Securely filled local byte buffers are eligible session-secret evidence.
            if function.endswith("rand.Read") and args:
                buffer_name = _identifier(args[0])
                if buffer_name in byte_buffers:
                    session_secrets[buffer_name] = line
                continue
            if function.endswith("io.ReadFull") and len(args) >= 2 and "rand.Reader" in args[0]:
                buffer_name = _identifier(args[1])
                if buffer_name in byte_buffers:
                    session_secrets[buffer_name] = line
                continue

            package_call = self._package_call(function)
            if package_call is not None:
                alias, method = package_call
                is_rsa_package = alias in rsa_aliases and alias not in shadowed_aliases

                if is_rsa_package and method in {"SignPKCS1v15", "SignPSS"} and len(args) >= 2:
                    key_name = _root_identifier(args[1])
                    if key_name in private_keys:
                        operations.append(_Operation(InferenceResult(
                            role=CryptoRole.SIGNATURE,
                            operation=CryptoOperation.SIGN,
                            confidence=ConfidenceLevel.DIRECT,
                            evidence=f"Line {line}: {function} consumes tracked RSA private key '{key_name}'.",
                            evidence_line=line,
                        ), key_name))
                    continue

                if is_rsa_package and method in {"VerifyPKCS1v15", "VerifyPSS"} and args:
                    key_name = _root_identifier(args[0])
                    if key_name in public_keys or key_name in private_keys:
                        operations.append(_Operation(InferenceResult(
                            role=CryptoRole.SIGNATURE,
                            operation=CryptoOperation.VERIFY,
                            confidence=ConfidenceLevel.DIRECT,
                            evidence=f"Line {line}: {function} consumes tracked RSA public key '{key_name}'.",
                            evidence_line=line,
                        ), key_name))
                    continue

                encrypt_indexes = {
                    "EncryptOAEP": (2, 3),
                    "EncryptPKCS1v15": (1, 2),
                }
                if is_rsa_package and method in encrypt_indexes:
                    key_index, plaintext_index = encrypt_indexes[method]
                    if len(args) <= plaintext_index:
                        continue
                    key_name = _root_identifier(args[key_index])
                    plaintext = _identifier(args[plaintext_index])
                    tracked_public = key_name in public_keys or key_name in private_keys
                    if not tracked_public:
                        continue
                    if plaintext in session_secrets:
                        result = InferenceResult(
                            role=CryptoRole.KEY_TRANSPORT,
                            operation=CryptoOperation.ENCRYPT,
                            confidence=ConfidenceLevel.DIRECT,
                            evidence=(
                                f"Line {line}: {function} encrypts tracked session secret "
                                f"'{plaintext}' filled from crypto/rand on line {session_secrets[plaintext]}."
                            ),
                            evidence_line=line,
                        )
                    else:
                        result = InferenceResult(
                            role=CryptoRole.ENCRYPTION,
                            operation=CryptoOperation.ENCRYPT,
                            confidence=ConfidenceLevel.INFERRED,
                            evidence=(
                                f"Line {line}: {function} encrypts data whose session-key purpose is unresolved."
                            ),
                            evidence_line=line,
                        )
                    operations.append(_Operation(result, key_name or "<expression>"))
                    continue

            # Methods on a proven key are also semantically meaningful.
            method_match = re.fullmatch(
                r"(?P<receiver>[A-Za-z_][A-Za-z0-9_]*)\.(?P<method>Sign|Decrypt)",
                function,
            )
            if not method_match:
                continue
            key_name = method_match.group("receiver")
            method = method_match.group("method")
            if key_name not in private_keys:
                continue
            if method == "Sign":
                result = InferenceResult(
                    role=CryptoRole.SIGNATURE,
                    operation=CryptoOperation.SIGN,
                    confidence=ConfidenceLevel.DIRECT,
                    evidence=f"Line {line}: tracked RSA private key '{key_name}' is used by .Sign().",
                    evidence_line=line,
                )
            else:
                result = InferenceResult(
                    role=CryptoRole.ENCRYPTION,
                    operation=CryptoOperation.DECRYPT,
                    confidence=ConfidenceLevel.INFERRED,
                    evidence=(
                        f"Line {line}: tracked RSA private key '{key_name}' decrypts data; "
                        "transport purpose is unresolved."
                    ),
                    evidence_line=line,
                )
            operations.append(_Operation(result, key_name))

        return operations

    def infer_rsa_usage(self) -> InferenceResult:
        if self.tree.root_node.has_error:
            return InferenceResult(evidence="Go syntax-tree parsing failed; role inference abstained.")

        rsa_aliases = self._rsa_import_aliases()
        if not rsa_aliases:
            return InferenceResult(evidence="No non-blank crypto/rsa import was resolved.")

        operations: list[_Operation] = []
        scopes = [
            node for node in _walk(self.tree.root_node)
            if node.type in {"function_declaration", "method_declaration"}
        ]
        for scope in scopes:
            operations.extend(self._analyze_scope(scope, rsa_aliases))

        if not operations:
            return InferenceResult(
                evidence="Go AST parsed, but no supported RSA operation was linked to a tracked key."
            )

        roles = {operation.result.role for operation in operations}
        if len(roles) != 1:
            evidence = "Conflicting Go RSA roles observed: " + "; ".join(
                operation.result.evidence for operation in operations
            )
            return InferenceResult(evidence=evidence)

        return min(operations, key=lambda operation: operation.result.evidence_line or 0).result


def infer_go_rsa_usage(source_code: str, filename: str = "<unknown>") -> InferenceResult:
    """Parse and analyze one Go source file, returning UNKNOWN on any parser failure."""

    try:
        return GoRoleAnalyzer(source_code, filename).infer_rsa_usage()
    except Exception as exc:  # Dependency/API failures must never produce a role guess.
        return InferenceResult(evidence=f"Go semantic analysis failed closed: {exc}")
