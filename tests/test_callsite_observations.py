"""Python import leads and executable call sites must remain distinct."""

from pqc_migration_tool.report.generator import build_project_report
from pqc_migration_tool.risk.scorer import score_system
from pqc_migration_tool.scanner.python_scanner import scan_file
from pqc_migration_tool.schema.models import CryptoOperation, CryptoRole


def _scan(tmp_path, source: str):
    path = tmp_path / "example.py"
    path.write_text(source, encoding="utf-8")
    findings = scan_file(str(path))
    report = build_project_report(score_system(str(tmp_path), findings, files_scanned=1))
    assert report.total_findings == len(report.records) == len(findings)
    return findings, report


def test_rsa_import_stays_an_inventory_lead(tmp_path) -> None:
    _, report = _scan(
        tmp_path,
        "from cryptography.hazmat.primitives.asymmetric import rsa\n",
    )
    assert len(report.records) == 1
    lead = report.records[0]
    assert lead.finding.detection_type == "import_lead"
    assert lead.finding.role == CryptoRole.UNKNOWN
    assert lead.plan.decision_trace.outcome.value == "abstain"


def test_rsa_operations_have_their_own_source_spans(tmp_path) -> None:
    source = (
        "import os\n"
        "from cryptography.hazmat.primitives.asymmetric import rsa\n"
        "def use_key(data):\n"
        "    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)\n"
        "    signature = key.sign(data, None, None)\n"
        "    session = os.urandom(32)\n"
        "    wrapped = key.public_key().encrypt(session, None)\n"
        "    return signature, wrapped\n"
    )
    findings, report = _scan(tmp_path, source)
    assert [(item.line, item.match_type) for item in findings if item.pattern.name == "RSA"] == [
        (2, "import"), (5, "linked_call"), (7, "linked_call")
    ]
    linked = [record.finding for record in report.records if record.finding.detection_type == "linked_operation"]
    assert {(item.location.line_number, item.role, item.operation) for item in linked} == {
        (5, CryptoRole.SIGNATURE, CryptoOperation.SIGN),
        (7, CryptoRole.KEY_TRANSPORT, CryptoOperation.ENCRYPT),
    }
    assert all(item.location.column is not None for item in linked)
    assert len({item.id for item in linked}) == 2
    assert [record.finding.role for record in report.records if record.finding.detection_type == "import_lead"] == [
        CryptoRole.UNKNOWN
    ]


def test_typed_rsa_calls_are_separate_from_import_lead(tmp_path) -> None:
    source = (
        "from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey\n"
        "def use(private: RSAPrivateKey, public: RSAPublicKey, data):\n"
        "    signature = private.sign(data, None, None)\n"
        "    public.verify(signature, data, None, None)\n"
    )
    _, report = _scan(tmp_path, source)
    linked = [record.finding for record in report.records if record.finding.detection_type == "linked_operation"]
    assert [(item.location.line_number, item.operation) for item in linked] == [
        (3, CryptoOperation.SIGN), (4, CryptoOperation.VERIFY)
    ]
    assert all(item.confidence.value == "inferred" for item in linked)


def test_repeated_and_aliased_hash_calls_are_not_deduplicated_by_file(tmp_path) -> None:
    source = (
        "import hashlib as h\n"
        "from hashlib import md5 as legacy_digest\n"
        "a = h.md5(b'a'); b = legacy_digest(b'b')\n"
    )
    findings, report = _scan(tmp_path, source)
    calls = [item for item in findings if item.pattern.name == "MD5 (hashlib)"]
    assert len(calls) == 2
    assert all(item.line == 3 and item.match_type == "call" for item in calls)
    assert len({item.col for item in calls}) == 2
    assert len({record.finding.id for record in report.records}) == 2


def test_unrelated_rsa_named_generator_does_not_create_linked_operation(tmp_path) -> None:
    source = (
        "import unrelated.rsa as r\n"
        "def use(data):\n"
        "    key = r.generate_private_key()\n"
        "    return key.sign(data)\n"
    )
    findings, report = _scan(tmp_path, source)
    assert findings == []
    assert report.records == []


def test_function_local_import_alias_does_not_leak_or_override_parameter(tmp_path) -> None:
    source = (
        "def real_hash(data):\n"
        "    import hashlib as local_hash\n"
        "    return local_hash.md5(data)\n"
        "def unrelated(local_hash):\n"
        "    return local_hash.md5(b'not necessarily crypto')\n"
    )
    findings, _ = _scan(tmp_path, source)
    calls = [item for item in findings if item.pattern.name == "MD5 (hashlib)"]
    assert [(item.line, item.match_type) for item in calls] == [(3, "call")]


def test_reassignment_stops_import_alias_resolution(tmp_path) -> None:
    source = (
        "import hashlib as digest_library\n"
        "a = digest_library.md5(b'first')\n"
        "digest_library = object()\n"
        "b = digest_library.md5(b'not proven crypto')\n"
    )
    findings, _ = _scan(tmp_path, source)
    calls = [item for item in findings if item.pattern.name == "MD5 (hashlib)"]
    assert [(item.line, item.match_type) for item in calls] == [(2, "call")]


def test_fully_qualified_rsa_import_resolves_generation(tmp_path) -> None:
    source = (
        "import cryptography.hazmat.primitives.asymmetric.rsa\n"
        "key = cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key(65537, 2048)\n"
        "signature = key.sign(b'data', None, None)\n"
    )
    _, report = _scan(tmp_path, source)
    linked = [record.finding for record in report.records if record.finding.detection_type == "linked_operation"]
    assert [(item.location.line_number, item.role) for item in linked] == [(3, CryptoRole.SIGNATURE)]


def test_ps256_jwt_call_is_linked_at_callsite(tmp_path) -> None:
    source = (
        "from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey\n"
        "import jwt\n"
        "def issue(key: RSAPrivateKey):\n"
        "    return jwt.encode({'sub': 'demo'}, key, algorithm='PS256')\n"
    )
    _, report = _scan(tmp_path, source)
    linked = [record.finding for record in report.records if record.finding.detection_type == "linked_operation"]
    assert [(item.location.line_number, item.role, item.operation) for item in linked] == [
        (4, CryptoRole.SIGNATURE, CryptoOperation.SIGN)
    ]
    assert linked[0].protocol_context.value == "jwt"


def test_safe_hash_is_not_mislabeled_as_standardized_pqc(tmp_path) -> None:
    _, report = _scan(tmp_path, "import hashlib\ndigest = hashlib.sha512(b'data')\n")
    assert len(report.records) == 1
    assert report.records[0].finding.status.value == "context_dependent"
    assert report.records[0].finding.role == CryptoRole.HASH


def test_actual_pqc_import_retains_standardized_status(tmp_path) -> None:
    _, report = _scan(tmp_path, "import pqcrypto.kem.ml_kem_768\n")
    assert len(report.records) == 1
    assert report.records[0].finding.status.value == "standardized_pqc"


def test_two_rsa_calls_on_one_line_have_distinct_ids(tmp_path) -> None:
    source = (
        "from cryptography.hazmat.primitives.asymmetric import rsa\n"
        "key = rsa.generate_private_key(public_exponent=65537, key_size=2048)\n"
        "a = key.sign(b'a', None, None); b = key.sign(b'b', None, None)\n"
    )
    _, report = _scan(tmp_path, source)
    linked = [record.finding for record in report.records if record.finding.detection_type == "linked_operation"]
    assert len(linked) == 2
    assert {item.location.line_number for item in linked} == {3}
    assert len({item.location.column for item in linked}) == 2
    assert len({item.id for item in linked}) == 2


def test_rebound_generated_key_does_not_gain_a_linked_role(tmp_path) -> None:
    source = (
        "from cryptography.hazmat.primitives.asymmetric import rsa\n"
        "key = rsa.generate_private_key(public_exponent=65537, key_size=2048)\n"
        "key = object()\n"
        "key.sign(b'data')\n"
    )
    _, report = _scan(tmp_path, source)
    assert not any(record.finding.detection_type == "linked_operation" for record in report.records)


def test_rebound_random_value_does_not_prove_key_transport(tmp_path) -> None:
    source = (
        "import os\n"
        "from cryptography.hazmat.primitives.asymmetric import rsa\n"
        "key = rsa.generate_private_key(public_exponent=65537, key_size=2048)\n"
        "session = os.urandom(32)\n"
        "session = b'ordinary data'\n"
        "key.public_key().encrypt(session, None)\n"
    )
    _, report = _scan(tmp_path, source)
    linked = [record.finding for record in report.records if record.finding.detection_type == "linked_operation"]
    assert [(item.role, item.operation) for item in linked] == [
        (CryptoRole.ENCRYPTION, CryptoOperation.ENCRYPT)
    ]
