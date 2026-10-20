"""Safety boundaries for RSA operation inference from Python type annotations."""

from pqc_migration_tool.resolver.context_inference import infer_rsa_operations, infer_rsa_usage
from pqc_migration_tool.schema.models import ConfidenceLevel, CryptoOperation, CryptoRole, ProtocolContext


RSA_IMPORT = "from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey\n"


def test_typed_private_sign_is_inferred_at_callsite() -> None:
    source = RSA_IMPORT + "def sign(key: RSAPrivateKey, data):\n    return key.sign(data, None, None)\n"
    result = infer_rsa_operations(source)[0]
    assert (result.role, result.operation, result.confidence, result.evidence_line) == (
        CryptoRole.SIGNATURE, CryptoOperation.SIGN, ConfidenceLevel.INFERRED, 3
    )
    assert "typed RSA private parameter" in result.evidence


def test_typed_public_verify_is_inferred() -> None:
    source = RSA_IMPORT + "def verify(key: RSAPublicKey, sig, data):\n    key.verify(sig, data, None, None)\n"
    result = infer_rsa_operations(source)[0]
    assert (result.role, result.operation, result.confidence) == (
        CryptoRole.SIGNATURE, CryptoOperation.VERIFY, ConfidenceLevel.INFERRED
    )


def test_import_alias_and_qualified_annotation_are_supported() -> None:
    source = (
        "from cryptography.hazmat.primitives.asymmetric import rsa as asymmetric_rsa\n"
        "def sign(key: asymmetric_rsa.RSAPrivateKey, data):\n"
        "    return key.sign(data, None, None)\n"
    )
    assert infer_rsa_operations(source)[0].operation == CryptoOperation.SIGN


def test_untrusted_or_rebound_parameter_abstains() -> None:
    sources = [
        "class RSAPrivateKey: pass\ndef sign(key: RSAPrivateKey):\n    key.sign(b'x')\n",
        RSA_IMPORT + "def sign(key: RSAPrivateKey, other):\n    key = other\n    key.sign(b'x')\n",
        RSA_IMPORT + "def sign(key: RSAPrivateKey):\n    del key\n    key.sign(b'x')\n",
        RSA_IMPORT + "def sign(key: RSAPrivateKey):\n    key.wrapper().sign(b'x')\n",
    ]
    for source in sources:
        assert infer_rsa_operations(source) == []
        assert infer_rsa_usage(source).role == CryptoRole.UNKNOWN


def test_incompatible_key_methods_abstain() -> None:
    source = RSA_IMPORT + (
        "def wrong(private: RSAPrivateKey, public: RSAPublicKey):\n"
        "    private.verify(b'x')\n"
        "    private.encrypt(b'x')\n"
        "    public.sign(b'x')\n"
        "    public.decrypt(b'x')\n"
    )
    assert infer_rsa_operations(source) == []


def test_multiple_calls_have_individual_evidence() -> None:
    source = RSA_IMPORT + (
        "def work(private: RSAPrivateKey, public: RSAPublicKey, data):\n"
        "    sig = private.sign(data, None, None)\n"
        "    public.verify(sig, data, None, None)\n"
    )
    results = infer_rsa_operations(source)
    assert [(item.operation, item.evidence_line) for item in results] == [
        (CryptoOperation.SIGN, 3), (CryptoOperation.VERIFY, 4)
    ]


def test_ps256_jwt_signing_with_typed_private_key() -> None:
    source = RSA_IMPORT + (
        "import jwt\n"
        "def issue(key: RSAPrivateKey):\n"
        "    return jwt.encode({'sub': 'example'}, key, algorithm='PS256')\n"
    )
    result = infer_rsa_usage(source)
    assert (result.role, result.operation, result.protocol_context, result.confidence) == (
        CryptoRole.SIGNATURE, CryptoOperation.SIGN, ProtocolContext.JWT, ConfidenceLevel.INFERRED
    )
