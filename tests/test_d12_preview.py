import hashlib
import json
import subprocess
import sys
from pathlib import Path

from pqc_migration_tool.patcher.preview import PreviewRequest, preview_md5_to_sha256


FIXTURES = Path(__file__).parent / "fixtures"
PROJECT = Path(__file__).parents[1]


def _request(path: Path, line: int | None = None, expected: str | None = None) -> PreviewRequest:
    digest = expected or hashlib.sha256(path.read_bytes()).hexdigest()
    return PreviewRequest(path, digest, line)


def test_exact_direct_call_generates_non_mutating_preview() -> None:
    path = FIXTURES / "d12_direct_md5.py"
    before = path.read_bytes()
    result = preview_md5_to_sha256(_request(path, line=5))

    assert result.status == "generated"
    assert "-digest = hashlib.md5" in result.diff
    assert "+digest = hashlib.sha256" in result.diff
    assert '-label = "hashlib.md5' not in result.diff
    assert '+label = "hashlib.sha256' not in result.diff
    assert '-# hashlib.md5' not in result.diff
    assert path.read_bytes() == before
    assert result.to_dict()["mutation_performed"] is False
    assert result.to_dict()["eligible_for_apply"] is False


def test_hash_mismatch_refuses() -> None:
    result = preview_md5_to_sha256(_request(FIXTURES / "d12_direct_md5.py", 5, "0" * 64))
    assert result.status == "refused"
    assert result.blocker_codes == ("D12_SOURCE_HASH_MISMATCH",)


def test_malformed_source_refuses(tmp_path: Path) -> None:
    path = tmp_path / "bad.py"
    path.write_text("import hashlib\ndigest = hashlib.md5(\n", encoding="utf-8")
    result = preview_md5_to_sha256(_request(path, 2))
    assert result.blocker_codes == ("D12_PARSE_FAILED",)


def test_alias_call_refuses() -> None:
    result = preview_md5_to_sha256(_request(FIXTURES / "d12_alias_md5.py", 3))
    assert result.blocker_codes == ("D12_AMBIGUOUS_HASHLIB_BINDING",)


def test_multiple_candidates_require_exact_line(tmp_path: Path) -> None:
    path = tmp_path / "two.py"
    path.write_text("import hashlib\na = hashlib.md5(b'a')\nb = hashlib.md5(b'b')\n", encoding="utf-8")
    ambiguous = preview_md5_to_sha256(_request(path))
    selected = preview_md5_to_sha256(_request(path, 3))
    assert ambiguous.blocker_codes == ("D12_CANDIDATE_NOT_UNIQUE",)
    assert selected.status == "generated"
    assert "-a = hashlib.md5" not in selected.diff
    assert "+a = hashlib.sha256" not in selected.diff
    assert "-b = hashlib.md5" in selected.diff


def test_shadowed_hashlib_refuses(tmp_path: Path) -> None:
    path = tmp_path / "shadowed.py"
    path.write_text("import hashlib\nhashlib = object()\nhashlib.md5(b'x')\n", encoding="utf-8")
    result = preview_md5_to_sha256(_request(path, 3))
    assert result.blocker_codes == ("D12_AMBIGUOUS_HASHLIB_BINDING",)


def test_generated_path_refuses(tmp_path: Path) -> None:
    generated = tmp_path / "generated"
    generated.mkdir()
    path = generated / "sample.py"
    path.write_text("import hashlib\nhashlib.md5(b'x')\n", encoding="utf-8")
    result = preview_md5_to_sha256(_request(path, 2))
    assert result.blocker_codes == ("D12_GENERATED_OR_VENDORED_PATH",)


def test_cli_writes_evidence_and_diff_without_touching_source(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("import hashlib\ndigest = hashlib.md5(b'x').hexdigest()\n", encoding="utf-8")
    before = source.read_bytes()
    expected = hashlib.sha256(before).hexdigest()
    output = tmp_path / "preview.json"
    patch = tmp_path / "preview.diff"
    completed = subprocess.run(
        [sys.executable, str(PROJECT / "cli.py"), "preview", str(source),
         "--expected-sha256", expected, "--line", "2",
         "--output", str(output), "--diff-output", str(patch)],
        cwd=PROJECT.parent,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["status"] == "generated"
    assert evidence["mutation_performed"] is False
    assert "hashlib.sha256" in patch.read_text(encoding="utf-8")
    assert source.read_bytes() == before
