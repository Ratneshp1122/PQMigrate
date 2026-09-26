from pathlib import Path

from pqc_migration_tool.resolver.context_inference import infer_rsa_usage
from pqc_migration_tool.schema.models import (
    ConfidenceLevel,
    CryptoOperation,
    CryptoRole,
    ProtocolContext,
)


FIXTURES = Path(__file__).parent / "fixtures" / "review"


def _infer(name: str):
    path = FIXTURES / name
    return infer_rsa_usage(path.read_text(encoding="utf-8"), str(path))


def test_links_generated_rsa_key_to_jwt_signature() -> None:
    result = _infer("review_rsa_jwt_signing.py")

    assert result.role == CryptoRole.SIGNATURE
    assert result.operation == CryptoOperation.SIGN
    assert result.protocol_context == ProtocolContext.JWT
    assert result.confidence == ConfidenceLevel.DIRECT
    assert "jwt.encode consumes tracked RSA key" in result.evidence


def test_links_rsa_encryption_to_generated_session_secret() -> None:
    result = _infer("review_rsa_key_transport.py")

    assert result.role == CryptoRole.KEY_TRANSPORT
    assert result.operation == CryptoOperation.ENCRYPT
    assert result.protocol_context == ProtocolContext.UNKNOWN
    assert result.confidence == ConfidenceLevel.DIRECT
    assert "encrypts tracked session secret" in result.evidence


def test_import_only_abstains() -> None:
    result = _infer("review_rsa_import_only.py")

    assert result.role == CryptoRole.UNKNOWN
    assert result.operation == CryptoOperation.UNKNOWN
    assert result.confidence == ConfidenceLevel.AMBIGUOUS


def test_same_function_proximity_does_not_link_unrelated_key() -> None:
    source = """
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

def issue_token(other_key):
    generated_but_unused = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return jwt.encode({"sub": "demo"}, other_key, algorithm="RS256")
"""

    result = infer_rsa_usage(source, "unrelated.py")

    assert result.role == CryptoRole.UNKNOWN
    assert result.confidence == ConfidenceLevel.AMBIGUOUS


def test_conflicting_roles_abstain() -> None:
    source = """
import os
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

def mixed_use():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode({"sub": "demo"}, key, algorithm="RS256")
    session_key = os.urandom(32)
    wrapped = key.public_key().encrypt(session_key, object())
    return token, wrapped
"""

    result = infer_rsa_usage(source, "mixed.py")

    assert result.role == CryptoRole.UNKNOWN
    assert result.confidence == ConfidenceLevel.AMBIGUOUS
    assert "Conflicting RSA roles observed" in result.evidence


def test_function_local_import_alias_does_not_leak_to_another_scope() -> None:
    source = """
def imports_rsa_locally():
    from cryptography.hazmat.primitives.asymmetric import rsa as local_rsa
    return local_rsa

def unrelated_scope(jwt, local_rsa):
    key = local_rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return jwt.encode({"sub": "demo"}, key, algorithm="RS256")
"""

    result = infer_rsa_usage(source, "local-import.py")

    assert result.role == CryptoRole.UNKNOWN
