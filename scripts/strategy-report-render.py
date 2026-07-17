#!/usr/bin/env python3
"""
strategy-report-render.py — General-Purpose Renderer für die Strategy-Pipeline.

Nimmt das konsolidierte JSON (vom Rust-Orchestrator) + ein HTML-Template
und rendert a 1-PDF-Report mit DYNAMISCHER, kontext-aware Länge.

Domän-agnostisch: funktioniert für jede Problemstellung, nicht nur Laura.

Mechanik der dynamischen Länge:
  - Das HTML wird an den .divider-Sektonen gesplittet.
  - Jede Sektion wird EINZELN mit Chrome-headless gerendert
    (break-before: page respektiert Chrome nur pro separat gerendertem Part).
  - Alle Parts werden mit pdfunite gemerged.
  - Die Seitenzahl ergibt sich aus der SUBSTANZ, nicht aus ainer Fix-Zahl.

Usage:
  python3 strategy-report-render.py <konsolidated.json> <output.pdf> [--html-template total_report_v2.html]
"""
import sys
import json
import pathlib
import subprocess
import tempfile
import os

CSS = """
  @page { size: A4; margin: 16mm 15mm 16mm 15mm; }
  * { box-sizing: border-box; }
  body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 10.5pt; line-height: 1.6; color: #1a1a1a; margin: 0; }
  h1 { font-size: 18pt; color: #0d3b2e; margin: 0 0 4px 0; }
  h2 { font-size: 13pt; color: #0d3b2e; border-bottom: 2px solid #2e7d32; padding-bottom: 3px; margin: 14px 0 8px; }
  h3 { font-size: 11pt; color: #1a1a1a; margin: 12px 0 4px; }
  h4 { font-size: 10pt; color: #333; margin: 8px 0 3px; font-style: italic; }
  p { margin: 5px 0; text-align: justify; }
  .stamp { font-size: 7pt; color: #555; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-bottom: 8px; }
  .subtitle { font-size: 9pt; color: #444; font-style: italic; margin: 0 0 8px; }
  .divider { background: #0d3b2e; color: #fff; padding: 6px 10px; font-size: 11pt; font-weight: bold; margin: 0 0 10px; border-radius: 3px; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 8.5pt; }
  th, td { border: 1px solid #bbb; padding: 3px 5px; text-align: left; vertical-align: top; }
  th { background: #e8f0e8; font-weight: bold; }
  .lens { background: #f6f9f6; border-left: 3px solid #2e7d32; padding: 6px 10px; margin: 7px 0; border-radius: 0 3px 3px 0; }
  .lens h3 { margin-top: 0; }
  .note-box { background: #fff4e6; border: 1px solid #ffb74d; padding: 6px 9px; margin: 7px 0; border-radius: 3px; }
  .evidence { background: #f4f6f9; border: 1px solid #90a4ae; padding: 6px 9px; margin: 7px 0; border-radius: 3px; font-size: 9pt; }
  .evidence b { color: #0d3b2e; }
  .reg { border-left: 4px solid #b71c1c; padding: 7px 11px; margin: 10px 0; background: #fdf3f3; border-radius: 0 3px 3px 0; }
  .reg-head { font-weight: bold; color: #b71c1c; font-size: 10pt; margin-bottom: 3px; }
  .reg-grid { display: grid; grid-template-columns: 115px 1fr; gap: 2px 7px; font-size: 8.5pt; margin-top: 3px; }
  .reg-grid b { color: #333; }
  .opt { background: #e8f0e8; padding: 3px 7px; margin: 2px 0; border-radius: 3px; font-size: 8.5pt; }
  .timeline { font-size: 8.5pt; border-left: 2px solid #2e7d32; padding-left: 10px; margin: 7px 0; }
  .timeline div { margin: 3px 0; }
  .timeline b { color: #0d3b2e; }
  .det { font-size: 8.5pt; margin-top: 4px; font-style: italic; color: #444; }
  .footer { font-size: 7pt; color: #666; border-top: 1px solid #ccc; margin-top: 14px; padding-top: 5px; }
  .disclaimer { font-size: 7pt; color: #666; font-style: italic; }
  ul { margin: 4px 0; padding-left: 18px; } li { margin: 2px 0; }
"""


def render_parts(html_path: pathlib.Path, workdir: pathlib.Path):
    """Split HTML at .divider, render each part separately, return PDF paths."""
    src = html_path.read_text(encoding="utf-8")
    # CSS extrahieren falls vorhanden, sonst Default-CSS
    import re
    m = re.search(r"<style>(.*?)</style>", src, re.S)
    css = m.group(1) if m else CSS
    chunks = re.split(r'(<div class="divider">.*?</div>)', src, flags=re.S)
    divs = [c for c in chunks if c.startswith('<div class="divider">')]
    cont = [c for c in chunks if not c.startswith('<div class="divider">') and c.strip()]

    parts = []
    # cont[0] = header+pre, dann abwechselnd cont[i] + divs[i-1]
    parts.append(cont[0] + (divs[0] if divs else "") + (cont[1] if len(cont) > 1 else ""))
    for i in range(1, len(divs)):
        c = cont[i + 1] if i + 1 < len(cont) else ""
        parts.append(divs[i] + c)

    pdfs = []
    for idx, body in enumerate(parts, 1):
        full = f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'
        hp = workdir / f"part_{idx}.html"
        pp = workdir / f"part_{idx}.pdf"
        hp.write_text(full, encoding="utf-8")
        r = subprocess.run(
            ["google-chrome-stable", "--headless", "--no-sandbox",
             "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={pp}", f"file://{hp}"],
            capture_output=True, text=True, timeout=120,
        )
        if pp.exists():
            pdfs.append(pp)
    return pdfs


def merge_pdfs(pdfs, out_path: pathlib.Path):
    if not pdfs:
        raise RuntimeError("Keine PDF-Parts gerendert")
    if len(pdfs) == 1:
        pdfs[0].replace(out_path)
        return
    cmd = ["pdfunite"] + [str(p) for p in pdfs] + [str(out_path)]
    subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 strategy-report-render.py <konsolidated.json> <output.pdf> [--html-template X.html]")
        sys.exit(1)
    json_path = pathlib.Path(sys.argv[1])
    out_path = pathlib.Path(sys.argv[2])
    template = None
    if "--html-template" in sys.argv:
        template = pathlib.Path(sys.argv[sys.argv.index("--html-template") + 1])

    # JSON laden (für Metadaten / Validierung)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    n_skills = data.get("n_skills", "?")
    consensus = data.get("consensus_score", "?")
    n_reg = len(data.get("failure_register", {}).get("eintraege", []))
    print(f"Konsolidated JSON: {n_skills} Skills, Consensus {consensus}%, {n_reg} Register-Einträge")

    # HTML-Template bestimmen
    if template and template.exists():
        html_path = template
    else:
        # Fallback: gleichnamig wie JSON aber .html
        html_path = json_path.with_suffix(".html")
    if not html_path.exists():
        print(f"FEHLER: Kein HTML-Template gefunden ({html_path})")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td)
        print(f"Rendere {html_path.name} (dynamische Länge)...")
        pdfs = render_parts(html_path, work)
        print(f"  {len(pdfs)} Sektionen gerendert")
        merge_pdfs(pdfs, out_path)

    # Seitenzahl prüfen
    r = subprocess.run(["file", str(out_path)], capture_output=True, text=True)
    print(f"  → {out_path.name}: {r.stdout.strip()}")
    print("FERTIG. Länge isch kontext-aware (Substanz bestimmt Seitenzahl).")


if __name__ == "__main__":
    main()
