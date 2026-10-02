import json
import re
from pathlib import Path

ROOT=Path(__file__).parents[1]
SITE=ROOT/"website"
PAGES={"index.html","how-it-works.html","demo.html","evaluation.html","benchmark.html","paper.html","docs.html"}

def test_required_pages_and_internal_links_resolve():
    assert {p.name for p in SITE.glob("*.html")}==PAGES
    for page in PAGES:
        text=(SITE/page).read_text(encoding="utf-8")
        assert 'name="viewport"' in text and 'class="skip"' in text and '<nav aria-label="Primary">' in text
        for link in re.findall(r'href="([^"]+)"',text):
            if link.startswith(("#","mailto:")): continue
            assert not link.startswith(("http://","https://"))
            assert (SITE/link.split("#")[0]).is_file(), f"{page}: broken {link}"

def test_no_upload_analytics_or_external_runtime():
    combined="\n".join(p.read_text(encoding="utf-8").lower() for p in SITE.rglob("*") if p.is_file())
    assert 'type="file"' not in combined and "google-analytics" not in combined and "gtag(" not in combined
    assert "https://" not in combined and "http://" not in combined

def test_fixed_sample_summary_matches_real_manifest():
    sample=json.loads((SITE/"data/sample-summary.json").read_text())
    manifest=json.loads((ROOT/"review-artifacts/latest/three-fixture-report.json").read_text())
    decisions=[(r.get("plan") or {}).get("decision_trace",{}).get("outcome") for r in manifest["records"]]
    assert sample["schema_version"]==manifest["schema_version"]
    assert sample["scan_id"]==manifest["scan_id"] and sample["source_commit"]==manifest["source_commit"]
    assert sample["files_scanned"]==manifest["files_scanned"] and sample["finding_count"]==len(manifest["records"])
    assert sample["recommend_count"]==decisions.count("recommend") and sample["abstain_count"]==decisions.count("abstain")

def test_claim_boundaries_are_visible():
    evaluation=(SITE/"evaluation.html").read_text(); benchmark=(SITE/"benchmark.html").read_text(); paper=(SITE/"paper.html").read_text()
    assert "No claim of real-world accuracy" in evaluation
    assert "no unverified performance headline" in benchmark
    assert "no publication, DOI, acceptance, or peer-review claim" in paper
