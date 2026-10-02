import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from pqc_migration_tool.dashboard.local_server import assurance, compare_manifests, create_server, patch_preview

def manifest(*ids):
    return {"schema_version":"test","source_commit":"abc123","files_scanned":2,"skipped_files":1,"records":[{"finding":{"id":item,"primitive_name":"MD5","location":{"file_path":"a.py","line_number":1}}} for item in ids]}

def test_missing_assurance_is_explicit_not_run(tmp_path):
    assert patch_preview(tmp_path)["status"] == "not_run"
    assert all(x["status"] == "not_run" for x in assurance(tmp_path,manifest("a"))["stages"])

def test_compare_separates_changed_findings_and_coverage():
    current=manifest("same","new"); previous=manifest("same","old"); previous["files_scanned"]=1
    result=compare_manifests(current,previous)
    assert result["new"]==["new"] and result["resolved"]==["old"] and result["unchanged"]==["same"]
    assert result["coverage"]["current"]["files_scanned"]==2

def test_d16_http_exports_and_pages(tmp_path):
    report=tmp_path/"scan.json"; report.write_text(json.dumps(manifest("x")),encoding="utf-8")
    (tmp_path/"d12-preview.json").write_text(json.dumps({"status":"generated","preview_sha256":"p"}),encoding="utf-8")
    server=create_server(report,port=0); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start(); base=f"http://127.0.0.1:{server.server_port}"
    try:
        html=urlopen(base).read().decode(); assert 'id="patch"' in html and 'id="assurance"' in html and 'id="export"' in html
        assert json.loads(urlopen(base+"/api/export?format=json").read())==manifest("x")
        assert "# PQMigrate saved scan" in urlopen(base+"/api/export?format=markdown").read().decode()
        try: urlopen(base+"/api/export?format=sarif")
        except HTTPError as exc: assert exc.code==404 and json.loads(exc.read())["status"]=="not_run"
        else: raise AssertionError("missing SARIF must not look successful")
    finally: server.shutdown(); server.server_close(); thread.join()

def test_static_ui_has_keyboard_loading_empty_and_error_states():
    root=Path(__file__).parents[1]/"dashboard"; html=(root/"index.html").read_text(); js=(root/"app.js").read_text()
    assert 'aria-live="polite"' in html and "loading" in html and "empty" in html
    assert 'e.key==="Enter"' in js and "className=\"error\"" in js and "status-not_run" in (root/"styles.css").read_text()
