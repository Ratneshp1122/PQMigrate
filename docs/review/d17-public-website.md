# D17 — Public research website

The `website/` directory is a dependency-free static site with Home, How it works, fixed interactive demo, Evaluation, Benchmark, Paper/related work, and Docs/releases pages.

The demo contains only the checked-in three-fixture result: three files, four findings, three recommendations, and one abstention. It accepts no uploads. The site loads no remote assets, includes no analytics, and labels the 72-case evaluation as a single-author synthetic pilot rather than a real-world accuracy result. D14 remains a controlled digest-compatibility result, not completed PQC/hybrid interoperability.

Validate with `bash scripts/run_d17_website.sh`, then preview with `python3 -m http.server 4173 --directory website`. D17 does not claim that static hosting or a packaged release has occurred.
