import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import pytest
from pqc_migration_tool.dashboard.local_server import create_server, load_manifest, manifest_summary

PROJECT = Path(__file__).parents[1]
def _fixture(tmp_path):
    root = tmp_path / "source"; root.mkdir(); (root / "sample.py").write_text("one\ntwo\nthree\nfour\nfive\n")
    manifest = tmp_path / "scan.json"
    manifest.write_text(json.dumps({"schema_version":"2.2","scan_id":"offline-fixture","source_commit":"abc123","files_scanned":1,"skipped_files":0,"records":[{"finding":{"id":"f1","role":"unknown"},"plan":{}}]}))
    return manifest, root

def test_manifest_validation_and_summary(tmp_path):
    manifest, _ = _fixture(tmp_path); summary = manifest_summary(load_manifest(manifest))
    assert summary["record_count"] == summary["unknown_role_count"] == 1 and summary["read_only"]

def test_dashboard_is_self_contained_and_has_pages_a_to_d():
    html = (PROJECT / "dashboard/index.html").read_text()
    assert "http://" not in html and "https://" not in html and "Apply Auto-Patch" not in html
    assert all(x in html for x in ('id="overview"','id="findings"','id="evidence"','id="planner"'))

def test_read_only_server_manifest_source_and_security(tmp_path):
    manifest, root = _fixture(tmp_path); server = create_server(manifest, root, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start(); base=f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base+"/api/manifest", timeout=3) as response:
            assert json.load(response)["scan_id"] == "offline-fixture"
            assert response.headers.get("Access-Control-Allow-Origin") is None
            assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        with urlopen(base+"/api/source?path=sample.py&line=3", timeout=3) as response:
            excerpt=json.load(response); assert [x["text"] for x in excerpt["lines"]]==["one","two","three","four","five"]
            assert sum(x["selected"] for x in excerpt["lines"]) == 1
        with pytest.raises(HTTPError) as escaped:
            urlopen(base+"/api/source?path=../scan.json&line=1", timeout=3)
        assert escaped.value.code == 403
        with pytest.raises(HTTPError) as write:
            urlopen(Request(base+"/api/manifest", data=b"{}", method="POST"), timeout=3)
        assert write.value.code == 405
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)

def test_non_loopback_binding_refuses(tmp_path):
    manifest, root = _fixture(tmp_path)
    with pytest.raises(ValueError, match="loopback"):
        create_server(manifest, root, bind="0.0.0.0", port=0)
