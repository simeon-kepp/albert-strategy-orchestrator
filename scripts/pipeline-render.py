#!/usr/bin/env python3
"""
pipeline-render.py — Hartes Render-Gate für die Strategy-Pipeline.

Läuft fact-audit.py VOR dem PDF-Render. Bei HARD FAIL: kein PDF, Lauf bricht ab.
Bei PASS: PDF wird gerendert (Chrome headless → pdfunite für Sektionen).

Usage:
  python3 pipeline-render.py <report.html> <facts.json> <output.pdf> [--consolidated JSON]
"""
import sys
import json
import pathlib
import subprocess
import tempfile
import re

FACT_AUDIT = pathlib.Path(
    "/home/eri-irfos/.hermes/skills/strategy/fact-audit/scripts/fact-audit.py"
)


def render(html_path: pathlib.Path, out_pdf: pathlib.Path):
    """Split-Render: jede Divider-Sektion als eigene PDF, dann pdfunite."""
    html = html_path.read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    chunks = re.split(r'(<div class="divider"[^>]*>.*?</div>)', html, flags=re.S)
    divs = [c for c in chunks if c.startswith('<div class="divider"')]
    cont = [c for c in chunks if not c.startswith('<div class="divider"') and c.strip()]
    parts = [cont[0] + divs[0] + cont[1]] + [
        divs[i] + (cont[i + 1] if i + 1 < len(cont) else "") for i in range(1, len(divs))
    ]
    pdfs = []
    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td)
        for idx, body in enumerate(parts, 1):
            full = f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'
            hp = work / f"p{idx}.html"
            pp = work / f"p{idx}.pdf"
            hp.write_text(full, encoding="utf-8")
            subprocess.run(
                ["google-chrome-stable", "--headless", "--no-sandbox",
                 "--disable-gpu", "--no-pdf-header-footer",
                 f"--print-to-pdf={pp}", f"file://{hp}"],
                capture_output=True, text=True, timeout=120,
            )
            if pp.exists():
                pdfs.append(pp)
        if len(pdfs) == 1:
            pdfs[0].replace(out_pdf)
        else:
            subprocess.run(
                ["pdfunite"] + [str(p) for p in pdfs] + [str(out_pdf)],
                capture_output=True, text=True, timeout=60,
            )
    return len(pdfs)


def main():
    if len(sys.argv) < 4:
        print("Usage: pipeline-render.py <report.html> <facts.json> <output.pdf>")
        sys.exit(2)

    html_path = pathlib.Path(sys.argv[1])
    facts_path = pathlib.Path(sys.argv[2])
    out_pdf = pathlib.Path(sys.argv[3])

    # GATE 1: Fact-Audit
    print("=== Pipeline-Render: Fact-Audit Gate ===")
    rc = subprocess.run(
        ["python3", str(FACT_AUDIT), str(html_path), str(facts_path)],
        capture_output=True, text=True,
    ).returncode
    if rc != 0:
        print("✗ FACT-AUDIT FEHLGESCHLAGEN — KEIN PDF ERZEUGT.")
        sys.exit(1)

    # GATE 2: Render
    print("=== Fact-Audit bestanden — Render ===")
    n = render(html_path, out_pdf)
    print(f"✓ PDF gerendert: {out_pdf.name} ({n} Sektionen)")


if __name__ == "__main__":
    main()
