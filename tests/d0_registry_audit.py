#!/usr/bin/env python3
"""
D0 Registry Audit Script
========================
Classifies all 62 patterns as:
  - import_lead       : import statement only, operation unknown (cannot safely auto-patch)
  - operation_candidate : contains a call/generate/sign/encrypt — operation partially knowable
  - configuration_lead : attribute/config access (e.g., ssl.PROTOCOL_TLSv1)

Also identifies the scan totals from the 3 baseline JSON scans.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pqc_migration_tool.scanner.patterns import (
    IMPORT_PATTERNS, CALL_PATTERNS, ATTRIBUTE_PATTERNS, Risk, Family
)
from pqc_migration_tool.scanner.go_patterns import GO_IMPORT_PATTERNS, GO_CALL_PATTERNS

OP_VERBS = [
    'sign', 'encrypt', 'decrypt', 'generate', 'exchange',
    'verify', 'mac', 'digest', 'hash', 'GenerateKey', 'Sign',
    'Encrypt', 'Decrypt', 'Exchange', 'New', 'Write', 'Sum',
]

results = []

# ── Python import patterns ─────────────────────────────────────────────────
for key, pat in sorted(IMPORT_PATTERNS.items()):
    is_op = any(v.lower() in key.lower() or v.lower() in pat.name.lower() for v in OP_VERBS)
    results.append({
        'lang': 'python', 'type': 'import_pattern', 'key': key,
        'name': pat.name, 'risk': pat.risk.value, 'family': pat.family.value,
        'classification': 'operation_candidate' if is_op else 'import_lead',
        'harvest_risk': pat.harvest_risk,
        'issue': 'import alone does not prove operation type — needs call-site resolution'
    })

# ── Python call patterns ───────────────────────────────────────────────────
for key, pat in sorted(CALL_PATTERNS.items()):
    results.append({
        'lang': 'python', 'type': 'call_pattern', 'key': key,
        'name': pat.name, 'risk': pat.risk.value, 'family': pat.family.value,
        'classification': 'operation_candidate',
        'harvest_risk': pat.harvest_risk,
        'issue': 'call detected but role (sign vs encrypt vs generate) still unresolved'
    })

# ── Python attribute patterns ──────────────────────────────────────────────
for key, pat in sorted(ATTRIBUTE_PATTERNS.items()):
    results.append({
        'lang': 'python', 'type': 'attribute_pattern', 'key': key,
        'name': pat.name, 'risk': pat.risk.value, 'family': pat.family.value,
        'classification': 'configuration_lead',
        'harvest_risk': pat.harvest_risk,
        'issue': 'config attribute — needs protocol role inference'
    })

# ── Go patterns ────────────────────────────────────────────────────────────
for key, pat in sorted(GO_IMPORT_PATTERNS.items()):
    is_op = any(v in key for v in OP_VERBS)
    results.append({
        'lang': 'go', 'type': 'import_pattern', 'key': key,
        'name': pat.name, 'risk': pat.risk.value, 'family': pat.family.value,
        'classification': 'operation_candidate' if is_op else 'import_lead',
        'harvest_risk': pat.harvest_risk,
        'issue': 'role unresolved — need dataflow to determine sign vs encrypt vs keygen'
    })

# Go call patterns are tuples (pattern_str, primitive_name, risk_label)
for item in GO_CALL_PATTERNS:
    if len(item) == 3:
        key, name, risk_label = item
    else:
        key, name, risk_label = item[0], str(item), 'CRITICAL'
    is_op = any(v in key for v in OP_VERBS)
    results.append({
        'lang': 'go', 'type': 'call_pattern', 'key': key,
        'name': name, 'risk': risk_label, 'family': 'asymmetric',
        'classification': 'operation_candidate' if is_op else 'import_lead',
        'harvest_risk': False,
        'issue': 'call detected but role still needs dataflow resolution'
    })

# ── Summary ────────────────────────────────────────────────────────────────
by_class   = {}
by_lang    = {}
dangerous  = []  # CRITICAL import_leads — cannot safely auto-patch
for r in results:
    by_class[r['classification']] = by_class.get(r['classification'], 0) + 1
    by_lang[r['lang']]            = by_lang.get(r['lang'], 0) + 1
    if r['risk'] == 'CRITICAL' and r['classification'] == 'import_lead':
        dangerous.append(r)

print("=" * 60)
print("  D0 Registry Audit — PQMigrate v0.3.0  (baseline commit 11dbc71)")
print("=" * 60)
print(f"\nTotal registry entries: {len(results)}")
print(f"  Python: {by_lang.get('python', 0)}")
print(f"  Go:     {by_lang.get('go', 0)}")
print(f"\nClassification breakdown:")
for k, v in sorted(by_class.items()):
    print(f"  {k:30s}: {v}")

print(f"\n{'─'*60}")
print(f"CRITICAL entries that are import_leads ({len(dangerous)}):")
print(f"  These CANNOT be safely auto-patched without operation inference.")
for d in dangerous:
    print(f"  [{d['lang']:6s}] {d['key'][:50]:52s}  → {d['name']}")

# ── Scan results from JSON logs ────────────────────────────────────────────
print(f"\n{'─'*60}")
print("Baseline scan results (reproduced at commit 11dbc71):")
scan_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'scan-logs')
for fname, label in [
    ('scan-paramiko-baseline.json', 'paramiko/paramiko'),
    ('scan-requests-baseline.json', 'psf/requests'),
    ('scan-vault-baseline.json',    'hashicorp/vault'),
]:
    fpath = os.path.join(scan_dir, fname)
    if os.path.exists(fpath):
        with open(fpath) as f:
            d = json.load(f)
        s = d.get('summary', d)
        print(f"\n  Repo: {label}")
        print(f"    files_scanned   : {s.get('files_scanned', '?')}")
        print(f"    critical_count  : {s.get('critical_count', '?')}")
        print(f"    high_count      : {s.get('high_count', '?')}")
        print(f"    medium_count    : {s.get('medium_count', '?')}")
        print(f"    system_risk_score: {s.get('system_risk_score', '?')}")
        print(f"    compliance_grade: {s.get('compliance_grade', '?')}")
    else:
        print(f"\n  {label}: LOG NOT FOUND at {fpath}")

# ── Known issues found during D0 ──────────────────────────────────────────
print(f"\n{'─'*60}")
print("Known issues identified in D0 audit:\n")
issues = [
    ("BUG-01", "CRITICAL", "All import patterns flagged as CRITICAL without operation proof",
     "import rsa ≠ RSA is used; needs call-site resolution (D3 work)"),
    ("BUG-02", "CRITICAL", "Single risk score collapses all evidence into one number",
     "Grade F not traceable to specific evidence; replace with dimension table (D8)"),
    ("BUG-03", "CRITICAL", "Patch rules: prior sprint planned RSA→ML-KEM auto-rewrite",
     "CANCELLED per roadmap §0. RSA sign/encrypt/wrap are different operations."),
    ("BUG-04", "CRITICAL", "Homegrown HKDF(X25519||MLKEM) combiner in demo files",
     "CANCELLED as migration recommendation. RFC 10024 only for TLS hybrid."),
    ("BUG-05", "MEDIUM",   "Deduplication by primitive name per file loses second usage location",
     "Two distinct RSA operations in same file collapse to one finding"),
    ("BUG-06", "MEDIUM",   "SHA-256 under Grover has 128-bit post-quantum security, not 'safe'",
     "Label as quantum_security_reduced, not SAFE for all contexts"),
    ("BUG-07", "LOW",      "vendored/generated code tracked in coverage/skip ledger not yet implemented",
     "Skipped files currently silently excluded — not recorded in output"),
    ("BUG-08", "LOW",      "No parser failure tracking — malformed .py/.go files silently skipped",
     "Needs coverage/skip ledger in output schema"),
]
for bug_id, sev, desc, fix in issues:
    print(f"  [{bug_id}] [{sev}] {desc}")
    print(f"           Fix: {fix}\n")

# ── Save full JSON ─────────────────────────────────────────────────────────
out_path = os.path.join(scan_dir, 'registry-audit-full.json')
with open(out_path, 'w') as f:
    json.dump({
        'baseline_commit': '11dbc71',
        'total_entries': len(results),
        'by_classification': by_class,
        'by_language': by_lang,
        'dangerous_import_leads': dangerous,
        'entries': results,
    }, f, indent=2)
print(f"\nFull audit saved → {out_path}")
