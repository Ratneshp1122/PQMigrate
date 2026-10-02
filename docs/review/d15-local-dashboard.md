# D15 — read-only local dashboard, pages A–D

- **Version:** `2026.10.02-d15.1`
- **Deployment:** loopback-only Python standard-library server
- **Data source:** one saved schema 2.2 scan manifest

The D15 workbench implements overview, deterministic findings filters with URL state, evidence detail with provenance and bounded source excerpts, and the advisory migration planner. Unknowns remain visible by default and every count has a complete manifest denominator.

The HTML, CSS, and JavaScript are repository-local and contain no CDN dependency. The server binds only to loopback, supplies no permissive CORS header, sends a restrictive content-security policy, rejects POST, restricts source access to the configured root, rejects traversal, and performs no upload or telemetry.

```bash
python3 cli.py dashboard --input review-artifacts/latest/three-fixture-report.json --source-root . --bind 127.0.0.1 --port 8765
```

D15 is read-only and serves one saved manifest. Patch preview and assurance screens E–G remain D16. Browser automation and a formal accessibility audit are not claimed; server/API behavior and required static structure are covered by automated tests.
