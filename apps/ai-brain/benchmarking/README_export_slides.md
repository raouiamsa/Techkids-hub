# Export slides and PDF — cs1000_co150

Files created:
- `strategy_final.py` — Python module that defines the canonical strategy and writes `strategy_final.json` when executed.
- `strategy_final.json` — canonical strategy to import in scripts.
- `slides/REPORT_cs1000_co150_slides.md` — markdown slides for Reveal.js.
- `slides/index.html` — Reveal.js wrapper loading the markdown slides.

Quick steps

1) Serve slides locally and open in browser

```powershell
# from repo root
cd apps/ai-brain/benchmarking/slides
python -m http.server 8000
# open http://localhost:8000/index.html in your browser
```

2) Produce a PDF from the slides (headless Chrome/Chromium)

```powershell
# from repo root (adjust chrome path as needed)
cd apps/ai-brain/benchmarking/slides
# start simple HTTP server first: python -m http.server 8000
# then run (example path for Chrome on Windows):
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --no-sandbox --print-to-pdf="../REPORT_cs1000_co150_slides.pdf" "http://localhost:8000/index.html"
```

Notes
- If you don't have Chrome locally, use any WebKit/Chromium-based browser with a `--print-to-pdf` or use `wkhtmltopdf`/`pandoc` as alternatives.
- The `strategy_final.json` can be loaded by `comp1_retrieval_ablation_runner.py` or other scripts to ensure consistent configurations.

Example: load strategy in Python

```python
import json
from pathlib import Path
s = json.loads(Path('apps/ai-brain/benchmarking/strategy_final.json').read_text())
print(s)
```
