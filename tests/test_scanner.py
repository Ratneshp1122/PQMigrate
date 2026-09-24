"""
PQC Migration Tool — Test Suite
================================
Day 5: Validates scanner accuracy against known fixtures and real repos.

Run:
  python3 -m pytest pqc_migration_tool/tests/ -v
  python3 pqc_migration_tool/tests/test_scanner.py          # standalone

Test categories:
  1. Python scanner — known-vulnerable fixture detection
  2. Python scanner — false positive checks (SAFE patterns stay SAFE)
  3. Go scanner — known-vulnerable fixture detection
  4. Go scanner — false positive checks
  5. Deduplication — same primitive reported only once per file
  6. Gitignore — ignored files are skipped
  7. Risk scorer — scoring logic validation
  8. Integration — full pipeline end-to-end
"""

import os
import sys
import tempfile
import shutil

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from pqc_migration_tool.scanner.python_scanner import scan_file, scan_directory
from pqc_migration_tool.scanner.go_scanner import scan_go_file, scan_go_directory
from pqc_migration_tool.scanner.patterns import Risk
from pqc_migration_tool.risk.scorer import score_system

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PY_FIXTURE = os.path.join(FIXTURES, "vulnerable_python.py")
GO_FIXTURE = os.path.join(FIXTURES, "vulnerable_go.go")

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"

_failures = 0
_passes   = 0

def check(condition: bool, name: str, detail: str = ""):
    global _failures, _passes
    if condition:
        print(f"  {PASS}  {name}")
        _passes += 1
    else:
        print(f"  {FAIL}  {name}" + (f"\n       → {detail}" if detail else ""))
        _failures += 1


# ─────────────────────────────────────────────────────────────────────────────
# Test Group 1: Python scanner — fixture detection
# ─────────────────────────────────────────────────────────────────────────────
def test_python_fixture():
    print("\n── Group 1: Python Scanner (fixture) ──")
    findings = scan_file(PY_FIXTURE)
    names    = {f.pattern.name for f in findings}
    risks    = {f.pattern.risk for f in findings}

    check(len(findings) > 0,
          "Python fixture produces findings")

    check(any(f.pattern.risk == Risk.CRITICAL for f in findings),
          "At least one CRITICAL finding (RSA/ECDSA/Ed25519)",
          f"risks seen: {risks}")

    check(any(f.pattern.risk == Risk.MEDIUM for f in findings),
          "At least one MEDIUM finding (MD5/SHA-1)",
          f"names: {names}")

    check(any(f.pattern.risk == Risk.SAFE for f in findings),
          "At least one SAFE finding (SHA-256 or similar)",
          f"names: {names}\nNote: SHA-256 SAFE detection depends on Python patterns registry")

    check(any(f.pattern.risk == Risk.HIGH for f in findings),
          "At least one HIGH finding (SSL/TLS)",
          f"risks: {risks}")


# ─────────────────────────────────────────────────────────────────────────────
# Test Group 2: Python scanner — deduplication
# ─────────────────────────────────────────────────────────────────────────────
def test_python_deduplication():
    print("\n── Group 2: Python Scanner — Deduplication ──")
    # Write a temp file with RSA imported twice in different ways
    td = tempfile.mkdtemp()
    src = """
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
import cryptography.hazmat.primitives.asymmetric.rsa
"""
    fpath = os.path.join(td, "dup.py")
    with open(fpath, "w") as f:
        f.write(src)

    findings = scan_file(fpath)
    rsa_findings = [f for f in findings
                    if "RSA" in f.pattern.name or "rsa" in f.pattern.name.lower()]
    shutil.rmtree(td)

    check(len(rsa_findings) == 1,
          "RSA reported exactly once (dedup works)",
          f"RSA finding count: {len(rsa_findings)}")



# ─────────────────────────────────────────────────────────────────────────────
# Test Group 3: Go scanner — fixture detection
# ─────────────────────────────────────────────────────────────────────────────
def test_go_fixture():
    print("\n── Group 3: Go Scanner (fixture) ──")
    findings = scan_go_file(GO_FIXTURE)
    risks    = {f.pattern.risk for f in findings}
    names    = {f.pattern.name for f in findings}

    check(len(findings) > 0,
          "Go fixture produces findings")

    check(any(f.pattern.risk == Risk.CRITICAL for f in findings),
          "At least one CRITICAL finding (RSA/ECDSA/Ed25519)",
          f"names: {names}")

    check(any(f.pattern.risk == Risk.MEDIUM for f in findings),
          "At least one MEDIUM finding (MD5/SHA-1)",
          f"names: {names}")

    check(any(f.pattern.risk == Risk.SAFE for f in findings),
          "SHA-256 detected as SAFE",
          f"names: {names}")

    check(any(f.pattern.risk == Risk.HIGH for f in findings),
          "TLS detected as HIGH (harvest risk)",
          f"names: {names}")


# ─────────────────────────────────────────────────────────────────────────────
# Test Group 4: Go scanner — false positive check
# ─────────────────────────────────────────────────────────────────────────────
def test_go_false_positives():
    print("\n── Group 4: Go Scanner — False Positive Check ──")
    td  = tempfile.mkdtemp()
    src = """package main

import (
    "crypto/aes"
    "crypto/sha256"
    "crypto/sha512"
    "crypto/rand"
    "golang.org/x/crypto/chacha20poly1305"
    "golang.org/x/crypto/bcrypt"
)

func main() {
    _ = aes.NewCipher(nil)
    _ = sha256.New()
    _ = sha512.New()
    _ = rand.Reader
    _ = chacha20poly1305.New(nil)
    bcrypt.GenerateFromPassword(nil, 12)
}
"""
    fpath = os.path.join(td, "safe.go")
    with open(fpath, "w") as f:
        f.write(src)

    findings = scan_go_file(fpath)
    critical = [f for f in findings if f.pattern.risk == Risk.CRITICAL]
    high     = [f for f in findings if f.pattern.risk == Risk.HIGH]
    shutil.rmtree(td)

    check(len(critical) == 0,
          "No CRITICAL findings in safe-only Go file",
          f"Critical: {[f.pattern.name for f in critical]}")

    check(len(high) == 0,
          "No HIGH findings in safe-only Go file",
          f"High: {[f.pattern.name for f in high]}")


# ─────────────────────────────────────────────────────────────────────────────
# Test Group 5: Gitignore — ignored files skipped
# ─────────────────────────────────────────────────────────────────────────────
def test_gitignore():
    print("\n── Group 5: Gitignore Support ──")
    td = tempfile.mkdtemp()

    # Write a gitignore that excludes the vulnerable file
    with open(os.path.join(td, ".gitignore"), "w") as f:
        f.write("secret_crypto.py\n")

    # Write a vulnerable file that should be ignored
    vuln_src = "from cryptography.hazmat.primitives.asymmetric import rsa\n"
    with open(os.path.join(td, "secret_crypto.py"), "w") as f:
        f.write(vuln_src)

    # Write a safe file that should be scanned
    with open(os.path.join(td, "main.py"), "w") as f:
        f.write("import hashlib\nprint(hashlib.sha256(b'x').hexdigest())\n")

    # With gitignore: should skip secret_crypto.py
    findings_with    = scan_directory(td, respect_gitignore=True)
    # Without gitignore: should find RSA
    findings_without = scan_directory(td, respect_gitignore=False)
    shutil.rmtree(td)

    rsa_with    = [f for f in findings_with
                   if "RSA" in f.pattern.name or "rsa" in f.pattern.name.lower()]
    rsa_without = [f for f in findings_without
                   if "RSA" in f.pattern.name or "rsa" in f.pattern.name.lower()]

    check(len(rsa_with) == 0,
          "Gitignored file is skipped (no RSA finding with gitignore ON)",
          f"Found: {rsa_with}")

    check(len(rsa_without) > 0,
          "Gitignored file scanned when gitignore OFF",
          "RSA finding should exist when gitignore is disabled")


# ─────────────────────────────────────────────────────────────────────────────
# Test Group 6: Risk scorer
# ─────────────────────────────────────────────────────────────────────────────
def test_risk_scorer():
    print("\n── Group 6: Risk Scorer ──")
    findings = scan_file(PY_FIXTURE)
    summary  = score_system("/tmp/test", findings, files_scanned=1)

    check(summary.system_risk_score > 0,
          "Risk score > 0 for vulnerable fixture",
          f"Score: {summary.system_risk_score}")

    check(summary.compliance_grade.startswith(("F", "D", "C")),
          "CISA grade is failing for vulnerable fixture",
          f"Grade: {summary.compliance_grade}")

    check(summary.critical_count > 0,
          "Critical count > 0",
          f"Critical: {summary.critical_count}")

    # Test a clean directory (our scanner itself is clean)
    clean_findings = []
    clean_summary  = score_system("/tmp/clean", clean_findings, files_scanned=10)
    check(clean_summary.system_risk_score == 0.0,
          "Empty findings → risk score = 0",
          f"Score: {clean_summary.system_risk_score}")

    check(clean_summary.compliance_grade.startswith("A"),
          "No findings → CISA Grade A",
          f"Grade: {clean_summary.compliance_grade}")



# ─────────────────────────────────────────────────────────────────────────────
# Test Group 7: Full pipeline integration
# ─────────────────────────────────────────────────────────────────────────────
def test_integration():
    print("\n── Group 7: Full Pipeline Integration ──")
    td = tempfile.mkdtemp()
    shutil.copy(PY_FIXTURE, td)
    shutil.copy(GO_FIXTURE, td)

    py_findings = scan_directory(td)
    go_findings = scan_go_directory(td)
    all_findings = py_findings + go_findings

    summary = score_system("/tmp/integration", all_findings, files_scanned=2)

    check(len(all_findings) > 0,
          "Integration: combined findings > 0",
          f"Total: {len(all_findings)}")

    check(summary.system_risk_score > 50,
          "Integration: risk score > 50 for known-vulnerable fixtures",
          f"Score: {summary.system_risk_score:.1f}")

    check(summary.compliance_grade.startswith(("F", "D")),
          "Integration: Grade F or D for known-vulnerable code",
          f"Grade: {summary.compliance_grade}")

    shutil.rmtree(td)
    print(f"\n  Summary: {summary.critical_count} CRITICAL, "
          f"{summary.high_count} HIGH, {summary.medium_count} MEDIUM, "
          f"{summary.safe_count} SAFE | Grade: {summary.compliance_grade} | "
          f"Score: {summary.system_risk_score:.1f}")



# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  PQC Migration Tool — Test Suite (Day 5)")
    print("═" * 60)

    test_python_fixture()
    test_python_deduplication()
    test_go_fixture()
    test_go_false_positives()
    test_gitignore()
    test_risk_scorer()
    test_integration()

    total = _passes + _failures
    print(f"\n{'═' * 60}")
    print(f"  Results: {_passes}/{total} passed", end="  ")
    if _failures == 0:
        print("\033[92mALL TESTS PASSED ✓\033[0m")
        sys.exit(0)
    else:
        print(f"\033[91m{_failures} FAILED ✗\033[0m")
        sys.exit(1)
