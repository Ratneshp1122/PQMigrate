from pathlib import Path

from pqc_migration_tool.report.generator import build_project_report
from pqc_migration_tool.resolver.go_semantic import (
    go_semantic_parser_available,
    infer_go_rsa_usage,
)
from pqc_migration_tool.risk.scorer import score_system
from pqc_migration_tool.scanner.go_scanner import scan_go_file
from pqc_migration_tool.schema.models import (
    ConfidenceLevel,
    CryptoOperation,
    CryptoRole,
)

FIXTURES = Path(__file__).parent / "fixtures" / "go_semantic"


def _infer_fixture(name: str):
    path = FIXTURES / name
    return infer_go_rsa_usage(path.read_text(encoding="utf-8"), str(path))


def test_go_parser_dependency_is_available() -> None:
    assert go_semantic_parser_available()


def test_alias_import_links_generated_key_to_signature() -> None:
    result = _infer_fixture("rsa_signature.go")

    assert result.role == CryptoRole.SIGNATURE
    assert result.operation == CryptoOperation.SIGN
    assert result.confidence == ConfidenceLevel.DIRECT
    assert "SignPSS consumes tracked RSA private key 'key'" in result.evidence


def test_links_rsa_encryption_to_crypto_rand_session_secret() -> None:
    result = _infer_fixture("rsa_key_transport.go")

    assert result.role == CryptoRole.KEY_TRANSPORT
    assert result.operation == CryptoOperation.ENCRYPT
    assert result.confidence == ConfidenceLevel.DIRECT
    assert "encrypts tracked session secret 'sessionKey'" in result.evidence


def test_import_only_abstains() -> None:
    result = _infer_fixture("rsa_import_only.go")

    assert result.role == CryptoRole.UNKNOWN
    assert result.operation == CryptoOperation.UNKNOWN
    assert result.confidence == ConfidenceLevel.AMBIGUOUS
    assert "no supported RSA operation" in result.evidence


def test_typed_rsa_parameter_links_method_signature() -> None:
    source = r'''
package demo
import (
    "crypto"
    "crypto/rand"
    "crypto/rsa"
)
func sign(key *rsa.PrivateKey, digest []byte) ([]byte, error) {
    return key.Sign(rand.Reader, digest, crypto.SHA256)
}
'''
    result = infer_go_rsa_usage(source, "typed-parameter.go")

    assert result.role == CryptoRole.SIGNATURE
    assert result.operation == CryptoOperation.SIGN
    assert result.confidence == ConfidenceLevel.DIRECT


def test_unrelated_key_does_not_infer_role() -> None:
    source = r'''
package demo
import (
    "crypto/rand"
    "crypto/rsa"
)
func sign(other *rsa.PrivateKey, digest []byte) ([]byte, error) {
    generatedButUnused, _ := rsa.GenerateKey(rand.Reader, 2048)
    _ = generatedButUnused
    return rsa.SignPSS(rand.Reader, other, 0, digest, nil)
}
'''
    # Explicitly typed parameters are valid semantic evidence, so make the
    # unrelated key untyped through an interface boundary instead.
    source = source.replace("other *rsa.PrivateKey", "other interface{}").replace(
        "rsa.SignPSS(rand.Reader, other,", "rsa.SignPSS(rand.Reader, other.(*rsa.PrivateKey),"
    )
    result = infer_go_rsa_usage(source, "unrelated.go")

    assert result.role == CryptoRole.UNKNOWN


def test_import_alias_shadowing_abstains() -> None:
    source = r'''
package demo
import crsa "crypto/rsa"
type fakeRSA struct{}
func (fakeRSA) SignPSS(...interface{}) ([]byte, error) { return nil, nil }
func sign() {
    crsa := fakeRSA{}
    _, _ = crsa.SignPSS(nil)
}
'''
    result = infer_go_rsa_usage(source, "shadow.go")

    assert result.role == CryptoRole.UNKNOWN


def test_conflicting_roles_abstain() -> None:
    source = r'''
package demo
import (
    "crypto/rand"
    "crypto/rsa"
    "crypto/sha256"
)
func mixed(digest []byte) {
    key, _ := rsa.GenerateKey(rand.Reader, 2048)
    _, _ = rsa.SignPSS(rand.Reader, key, 0, digest, nil)
    sessionKey := make([]byte, 32)
    _, _ = rand.Read(sessionKey)
    _, _ = rsa.EncryptOAEP(sha256.New(), rand.Reader, &key.PublicKey, sessionKey, nil)
}
'''
    result = infer_go_rsa_usage(source, "mixed.go")

    assert result.role == CryptoRole.UNKNOWN
    assert "Conflicting Go RSA roles observed" in result.evidence


def test_malformed_source_fails_closed() -> None:
    result = infer_go_rsa_usage(
        'package demo\nimport "crypto/rsa"\nfunc broken( {',
        "broken.go",
    )

    assert result.role == CryptoRole.UNKNOWN
    assert "parsing failed" in result.evidence


def test_project_report_uses_go_semantic_role(tmp_path: Path) -> None:
    path = tmp_path / "sign.go"
    path.write_text(r'''
package demo
import (
    "crypto/rand"
    "crypto/rsa"
)
func sign(digest []byte) ([]byte, error) {
    key, _ := rsa.GenerateKey(rand.Reader, 2048)
    return rsa.SignPSS(rand.Reader, key, 0, digest, nil)
}
''', encoding="utf-8")

    findings = scan_go_file(str(path))
    summary = score_system(str(tmp_path), findings, files_scanned=1)
    report = build_project_report(summary)

    rsa_records = [
        record for record in report.records
        if "rsa" in record.finding.primitive_name.lower()
    ]
    assert len(rsa_records) == 1
    assert rsa_records[0].finding.role == CryptoRole.SIGNATURE
    assert rsa_records[0].finding.detection_type == "linked_operation"
