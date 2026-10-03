from pathlib import Path
from pqc_migration_tool.release.readiness import assess
ROOT=Path(__file__).parents[1]
def test_faculty_packet_has_timed_demo_commands_and_claim_boundaries():
    text=(ROOT/"docs/review/d19-faculty-demo-packet.md").read_text(encoding="utf-8")
    for marker in ("0:00","2:00","4:00","6:00","8:00"): assert marker in text
    assert "scripts/validate_d0_d20.sh" in text
    assert "not product-wide accuracy" in text and "Automatic mutation remains disabled" in text
def test_release_readiness_never_claims_an_uncreated_tag():
    report=assess(ROOT); assert report["tag_name"]=="v0.1.0"
    if not report["tag_created"]:
        assert "D19_V0_1_TAG_NOT_CREATED" in report["blocker_codes"] and report["release_eligible"] is False
