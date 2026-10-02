"""Loopback-only, read-only D15/D16 dashboard for saved evidence."""
from __future__ import annotations
import json, mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

DASHBOARD_VERSION="2026.10.02-d16.1"; LOOPBACK_NAMES={"127.0.0.1","localhost","::1"}; MAX_BYTES=20*1024*1024

def _load(path: Path)->Any:
    if not path.exists() or not path.is_file() or path.is_symlink(): raise ValueError(f"invalid evidence file: {path.name}")
    if path.stat().st_size>MAX_BYTES: raise ValueError("evidence exceeds 20 MiB")
    return json.loads(path.read_text(encoding="utf-8"))

def load_manifest(path: Path)->dict[str,Any]:
    data=_load(path)
    if not isinstance(data,dict) or not isinstance(data.get("records"),list): raise ValueError("manifest must contain a records array")
    return data

def manifest_summary(data):
    records=data["records"]
    return {"dashboard_version":DASHBOARD_VERSION,"schema_version":data.get("schema_version"),"scan_id":data.get("scan_id"),"source_commit":data.get("source_commit"),"files_scanned":data.get("files_scanned",0),"skipped_files":data.get("skipped_files",0),"record_count":len(records),"unknown_role_count":sum((r.get("finding") or {}).get("role")=="unknown" for r in records),"read_only":True}

def _optional(path):
    try:
        value=_load(path); return value if isinstance(value,dict) else None
    except (ValueError,OSError,json.JSONDecodeError): return None

def patch_preview(folder):
    return _optional(folder/"d12-preview.json") or {"status":"not_run","eligible_for_apply":False,"mutation_performed":False,"blocker_codes":["D12_EVIDENCE_NOT_AVAILABLE"],"diff":"","explanation":"Run D12 to create d12-preview.json."}

def assurance(folder,manifest):
    d12=_optional(folder/"d12-preview.json"); d13=_optional(folder/"d13-verification.json"); d14=_optional(folder/"d14-interoperability.json")
    def stage(name,data,ok):
        raw=data.get("status","unknown") if data else "not_run"
        return {"name":name,"status":"pass" if raw in ok else ("not_run" if raw=="not_run" else "fail"),"reported_status":raw,"schema_version":data.get("schema_version") if data else None}
    return {"status":"evidence_available" if any((d12,d13,d14)) else "not_run","source_commit":manifest.get("source_commit") or "unknown","patch_hash":(d13 or d12 or {}).get("preview_sha256"),"stages":[stage("Patch preview",d12,{"generated"}),stage("Isolated verification",d13,{"verified_bounded"}),stage("Bounded interoperability",d14,{"pass_bounded"})],"checks":d13.get("checks",{}) if d13 else {},"test_command":d13.get("test_command") if d13 else None,"test_exit_code":d13.get("test_exit_code") if d13 else None,"environment":d14.get("environment") if d14 else None,"limitations":(d13.get("limitations",[]) if d13 else [])+(d14.get("not_claimed",[]) if d14 else [])}

def compare_manifests(current,previous):
    def ids(data): return {str((r.get("finding") or {}).get("id")) for r in (data or {}).get("records",[]) if (r.get("finding") or {}).get("id") is not None}
    a,b=ids(current),ids(previous)
    return {"status":"compared" if previous is not None else "not_run","new":sorted(a-b),"resolved":sorted(b-a),"unchanged":sorted(a&b),"coverage":{"current":{"files_scanned":current.get("files_scanned",0),"skipped_files":current.get("skipped_files",0)},"previous":{"files_scanned":previous.get("files_scanned",0),"skipped_files":previous.get("skipped_files",0)} if previous else None}}

def _markdown(data):
    out=["# PQMigrate saved scan","",f"- Scan: `{data.get('scan_id','unknown')}`",f"- Source commit: `{data.get('source_commit','unknown')}`",f"- Files scanned: {data.get('files_scanned',0)}",f"- Findings: {len(data.get('records',[]))}","","## Findings",""]
    for r in data.get("records",[]):
        f=r.get("finding") or {}; loc=f.get("location") or {}; out.append(f"- `{f.get('id','unknown')}` — {f.get('primitive_name','unknown')} at `{loc.get('file_path','?')}:{loc.get('line_number','?')}`")
    return "\n".join(out)+"\n"

def _excerpt(root,requested,line):
    if root is None: raise PermissionError("source navigation is disabled")
    root=root.resolve(); raw=Path(requested); target=(raw if raw.is_absolute() else root/raw)
    if target.is_symlink(): raise PermissionError("source symlinks are not allowed")
    target=target.resolve()
    try: relative=target.relative_to(root)
    except ValueError as exc: raise PermissionError("source path escapes configured root") from exc
    if not target.is_file() or target.stat().st_size>1024*1024: raise PermissionError("source path is not an allowed regular file")
    lines=target.read_text(encoding="utf-8",errors="replace").splitlines()
    if line<1 or line>len(lines): raise ValueError("line is outside the source file")
    start,end=max(1,line-2),min(len(lines),line+2)
    return {"path":relative.as_posix(),"requested_line":line,"start_line":start,"end_line":end,"lines":[{"number":n,"text":lines[n-1],"selected":n==line} for n in range(start,end+1)]}

def create_server(manifest_path:Path,source_root:Path|None=None,bind="127.0.0.1",port=8765,compare_manifest_path:Path|None=None):
    if bind not in LOOPBACK_NAMES: raise ValueError("dashboard may bind only to a loopback address")
    manifest=load_manifest(manifest_path); previous=load_manifest(compare_manifest_path) if compare_manifest_path else None; assets=Path(__file__).resolve().parent; folder=manifest_path.resolve().parent; root=source_root.resolve() if source_root else None
    class Handler(BaseHTTPRequestHandler):
        server_version="PQMigrateDashboard/2"
        def _send(self,status,body,kind):
            self.send_response(status); self.send_header("Content-Type",kind); self.send_header("Content-Length",str(len(body))); self.send_header("Cache-Control","no-store"); self.send_header("X-Content-Type-Options","nosniff"); self.send_header("X-Frame-Options","DENY"); self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'"); self.end_headers(); self.wfile.write(body)
        def _json(self,status,value): self._send(status,(json.dumps(value,indent=2,sort_keys=True)+"\n").encode(),"application/json; charset=utf-8")
        def do_GET(self):
            p=urlparse(self.path)
            if p.path=="/api/manifest": self._json(200,manifest); return
            if p.path=="/api/summary": self._json(200,manifest_summary(manifest)); return
            if p.path=="/api/patch-preview": self._json(200,patch_preview(folder)); return
            if p.path=="/api/assurance": self._json(200,assurance(folder,manifest)); return
            if p.path=="/api/compare": self._json(200,compare_manifests(manifest,previous)); return
            if p.path=="/api/export":
                fmt=parse_qs(p.query).get("format",["json"])[0]
                if fmt=="json": self._json(200,manifest); return
                if fmt=="markdown": self._send(200,_markdown(manifest).encode(),"text/markdown; charset=utf-8"); return
                names={"sarif":"three-fixture.sarif.json","cbom":"three-fixture.cdx.json"}
                if fmt not in names: self._json(400,{"error":"format must be json, sarif, cbom, or markdown"}); return
                value=_optional(folder/names[fmt])
                if value is None: self._json(404,{"status":"not_run","error":f"{fmt} export evidence is unavailable"}); return
                self._json(200,value); return
            if p.path=="/api/source":
                q=parse_qs(p.query)
                try: value=_excerpt(root,q.get("path",[""])[0],int(q.get("line",["0"])[0]))
                except PermissionError as exc: self._json(HTTPStatus.FORBIDDEN,{"error":str(exc)})
                except (ValueError,OSError) as exc: self._json(HTTPStatus.BAD_REQUEST,{"error":str(exc)})
                else: self._json(200,value)
                return
            asset="index.html" if p.path=="/" else p.path.removeprefix("/")
            if asset not in {"index.html","app.js","styles.css"}: self._json(404,{"error":"not found"}); return
            body=(assets/asset).read_bytes(); self._send(200,body,f"{mimetypes.guess_type(asset)[0] or 'application/octet-stream'}; charset=utf-8")
        def do_POST(self): self._json(405,{"error":"dashboard is read-only"})
        do_PUT=do_POST; do_PATCH=do_POST; do_DELETE=do_POST
        def log_message(self,format,*args): return
    return ThreadingHTTPServer((bind,port),Handler)
