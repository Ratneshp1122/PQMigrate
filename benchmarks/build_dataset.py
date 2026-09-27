"""Build the versioned synthetic D9 pilot dataset.

The generator is committed with the JSONL output so every parameterized case
and gold label can be reviewed. It does not execute any target snippet.
"""

from __future__ import annotations

import json
from pathlib import Path


VERSION = "pqmigratebench-0.1.0"
OUTPUT = Path(__file__).with_name("pqmigratebench_v0_1.jsonl")


def _split(index: int) -> str:
    """Give every scenario family held-out coverage (roughly 70/15/15)."""
    marker = index % 6
    return "dev" if marker == 0 else "test" if marker == 1 else "train"


def _case(
    case_id: str,
    index: int,
    category: str,
    source: str,
    *,
    is_operation: bool,
    role: str = "unknown",
    operation: str = "unknown",
    protocol_context: str = "unknown",
    confidence: str = "ambiguous",
    rationale: str,
    accounting: str = "evaluated",
) -> dict:
    return {
        "benchmark_version": VERSION,
        "id": case_id,
        "split": _split(index),
        "language": "python",
        "scope": "bounded_rsa_role_inference",
        "category": category,
        "accounting": accounting,
        "label_status": "single_author_synthetic_pilot",
        "source": source.strip() + "\n",
        "gold": {
            "is_operation": is_operation,
            "role": role,
            "operation": operation,
            "protocol_context": protocol_context,
            "confidence": confidence,
        },
        "rationale": rationale,
    }


def build_cases() -> list[dict]:
    cases: list[dict] = []

    signature_calls = [
        ("sign", "sign"),
        ("public_key().verify", "verify"),
        ("sign", "sign"),
    ]
    rsa_imports = [
        "from cryptography.hazmat.primitives.asymmetric import rsa",
        "from cryptography.hazmat.primitives.asymmetric import rsa as asymmetric_rsa",
    ]
    for index in range(12):
        call, operation = signature_calls[index % len(signature_calls)]
        import_line = rsa_imports[index % len(rsa_imports)]
        module_name = "rsa" if " as " not in import_line else "asymmetric_rsa"
        cases.append(_case(
            f"sig-direct-{index + 1:03d}", index, "signature_direct",
            f"""
{import_line}

def operation_{index}():
    key = {module_name}.generate_private_key(public_exponent=65537, key_size=2048)
    return key.{call}(b'message', object())
""",
            is_operation=True, role="signature", operation=operation,
            confidence="direct",
            rationale="A generated RSA key is consumed by a same-scope sign or verify call.",
        ))

    jwt_imports = [
        ("import jwt", "jwt.encode"),
        ("import jwt as tokenlib", "tokenlib.encode"),
        ("from jwt import encode as issue", "issue"),
        ("from jwt import encode", "encode"),
    ]
    algorithms = ["RS256", "RS384", "RS512", "rs256"]
    for index in range(8):
        jwt_import, call = jwt_imports[index % len(jwt_imports)]
        algorithm = algorithms[index % len(algorithms)]
        cases.append(_case(
            f"sig-jwt-{index + 1:03d}", index, "signature_jwt",
            f"""
{jwt_import}
from cryptography.hazmat.primitives.asymmetric import rsa

def issue_{index}():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return {call}({{'sub': 'case-{index}'}}, key, algorithm='{algorithm}')
""",
            is_operation=True, role="signature", operation="sign",
            protocol_context="jwt", confidence="direct",
            rationale="JWT encode consumes the tracked RSA key with an RS* algorithm.",
        ))

    secret_sources = [
        ("import os", "os.urandom(32)"),
        ("import os as operating", "operating.urandom(32)"),
        ("import secrets", "secrets.token_bytes(32)"),
        ("import secrets as secure", "secure.token_bytes(24)"),
    ]
    for index in range(12):
        secret_import, secret_call = secret_sources[index % len(secret_sources)]
        cases.append(_case(
            f"transport-{index + 1:03d}", index, "key_transport",
            f"""
{secret_import}
from cryptography.hazmat.primitives.asymmetric import rsa

def wrap_{index}():
    recipient = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    session_secret = {secret_call}
    return recipient.public_key().encrypt(session_secret, object())
""",
            is_operation=True, role="key_transport", operation="encrypt",
            confidence="direct",
            rationale="RSA encrypts a same-scope secret from an approved random-byte source.",
        ))

    encryption_calls = [
        ("key.public_key().encrypt(payload, object())", "encrypt"),
        ("key.decrypt(payload, object())", "decrypt"),
        ("key.public_key().encrypt(document, object())", "encrypt"),
        ("key.decrypt(document, object())", "decrypt"),
    ]
    for index in range(8):
        call, operation = encryption_calls[index % len(encryption_calls)]
        data_name = "document" if "document" in call else "payload"
        cases.append(_case(
            f"encryption-{index + 1:03d}", index, "asymmetric_encryption",
            f"""
from cryptography.hazmat.primitives.asymmetric import rsa

def encrypt_{index}():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    {data_name} = b'application-data'
    return {call}
""",
            is_operation=True, role="encryption", operation=operation,
            confidence="inferred",
            rationale="RSA encrypt/decrypt is observed but session-key purpose is not established.",
        ))

    negative_sources = [
        "from cryptography.hazmat.primitives.asymmetric import rsa",
        "from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(public_exponent=65537, key_size=2048)",
        """
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
def issue(other_key):
    unused = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return jwt.encode({'sub': 'x'}, other_key, algorithm='RS256')
""",
        """
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
def issue():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return jwt.encode({'sub': 'x'}, key, algorithm='HS256')
""",
        """
from cryptography.hazmat.primitives.asymmetric import rsa
key.sign(b'message', object())
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
""",
        """
def local_import():
    from cryptography.hazmat.primitives.asymmetric import rsa as local_rsa
    return local_rsa
def other_scope(jwt, local_rsa):
    key = local_rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return jwt.encode({'sub': 'x'}, key, algorithm='RS256')
""",
        """
import os
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
def mixed():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    signed = jwt.encode({'sub': 'x'}, key, algorithm='RS256')
    secret = os.urandom(32)
    wrapped = key.public_key().encrypt(secret, object())
    return signed, wrapped
""",
        """
class rsa:
    @staticmethod
    def generate_private_key(**kwargs):
        return object()
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
""",
    ]
    for index in range(16):
        cases.append(_case(
            f"negative-{index + 1:03d}", index, "negative_control",
            negative_sources[index % len(negative_sources)],
            is_operation=False,
            rationale="No identity-linked, unambiguous supported RSA operation is present.",
        ))

    parse_failures = [
        "def broken(:\n    pass",
        "from cryptography.hazmat.primitives.asymmetric import rsa\nkey = (",
        "if True print('broken')",
        "def incomplete():\n    return [1, 2",
    ]
    for index, source in enumerate(parse_failures):
        cases.append(_case(
            f"parse-failure-{index + 1:03d}", index, "parse_failure", source,
            is_operation=False,
            rationale="Invalid syntax must be reported separately and must not become an answered role.",
            accounting="parse_failure",
        ))

    unsupported_sources = [
        ("key.sign(b'message', object())", "signature", "sign"),
        ("key.verify(b'sig', b'message', object())", "signature", "verify"),
        ("key.public_key().encrypt(b'data', object())", "encryption", "encrypt"),
        ("key.decrypt(b'ciphertext', object())", "encryption", "decrypt"),
        ("alias.sign(b'message', object())", "signature", "sign"),
        ("alias.public_key().encrypt(b'data', object())", "encryption", "encrypt"),
    ]
    for index in range(12):
        call, role, operation = unsupported_sources[index % len(unsupported_sources)]
        alias_line = "alias = key" if call.startswith("alias") else "alias = None"
        cases.append(_case(
            f"unsupported-valid-{index + 1:03d}", index, "unsupported_valid_operation",
            f"""
def use_loaded_key(key):
    {alias_line}
    return {call}
""",
            is_operation=True, role=role, operation=operation,
            confidence="direct",
            rationale="The operation is valid gold evidence, but D9's bounded resolver does not track parameter or alias origins.",
        ))

    assert len(cases) == 72
    assert len({case["id"] for case in cases}) == len(cases)
    return cases


def main() -> None:
    cases = build_cases()
    OUTPUT.write_text(
        "".join(json.dumps(case, sort_keys=True) + "\n" for case in cases),
        encoding="utf-8",
    )
    counts = {split: sum(case["split"] == split for case in cases) for split in ("train", "dev", "test")}
    print(f"Wrote {len(cases)} cases to {OUTPUT} ({counts}).")


if __name__ == "__main__":
    main()

