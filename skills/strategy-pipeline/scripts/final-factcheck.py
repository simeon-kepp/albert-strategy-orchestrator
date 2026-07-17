#!/usr/bin/env python3
"""
final-factcheck.py — Extra Fact-Checker Gate BEVOR der Endreport rausgeht.

Läuft NACH der Report-Generierung, VOR dem PDF-Render (zwischen HTML-Write
und pipeline-render). Liest den VOLLEN Report kontextuell durch und
cross-checkt jede Fakt-Behauptung gegen die Quell-Docs (00/02/03/04).

Zwei Modi:
  --mode pattern   : deterministisch, schnell (Personen/Anzeige/Framework)
  --mode llm       : delegiert an Subagent (kontextuell, tief) — braucht Hermes

Exit 0 = OK (weiter zum Render).
Exit 1 = HARD FAIL (Konflikt gefunden, KEIN PDF).

Usage:
  python3 final-factcheck.py <report.html> <facts.json> [--sources dir] [--mode pattern]
"""
import sys
import json
import pathlib
import re
import subprocess
import tempfile
import shlex

# Framework-Namen (HARD FAIL im Report)
FORBIDDEN_FRAMEWORKS = [
    "Gabor Maté", "Gabor Mate", "Sun Tzu", "Sun Mate",
    "OODA", "Game Theory", "Systems Thinking",
]
FORBIDDEN_BRANDS = ["Linsen", "Laura-Pipeline"]

# Anzeige-Verben
ANZEIGE_VERBS = [
    "anzeige gegen", "anzeige erstattet", "erstattete anzeige",
    "zeigte an", "klagte", "anzeigenerstatter", "anzeigebereit",
]


def strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def pattern_check(text: str, facts: dict) -> list:
    """Deterministischer Check: Personen + Framework + Brand."""
    errors = []
    entities = facts.get("entities", {})

    # 1) Anzeige-Bereitschaft
    for name, meta in entities.items():
        if not meta.get("anzeigebereit", False):
            first = name.split()[0].lower()
            if first in text.lower():
                idx = text.lower().find(first)
                ctx = text.lower()[max(0, idx - 50): idx + len(name) + 50]
                if any(v in ctx for v in ANZEIGE_VERBS):
                    errors.append(
                        f"HARD FAIL [Person]: '{name}' (anzeigebereit=false) "
                        f"mit Anzeige-Verb. Quelle: {meta.get('quelle','?')}"
                    )

    # 2) Framework-Namen
    for fw in FORBIDDEN_FRAMEWORKS:
        if fw.lower() in text.lower():
            errors.append(f"HARD FAIL [Framework]: '{fw}' im Report.")

    # 3) Brand
    for br in FORBIDDEN_BRANDS:
        if br.lower() in text.lower():
            errors.append(f"HARD FAIL [Brand]: '{br}' im Report.")

    return errors


def llm_check(report_path: pathlib.Path, sources_dir: pathlib.Path, facts: dict) -> list:
    """Echter kontextueller Deep-Check via Hermes `chat` (non-interactive).

    Ruft `hermes chat -q ... -Q` auf — der Subagent liest den vollen Report
    und cross-checkt ihn gegen die Quell-Docs. Retourniert bei Konflikten
    Zeilen die mit 'KONFLIKT:' beginnen.
    """
    # Quell-Docs als Kontext mitgeben (falls vorhanden)
    src_files = sorted(sources_dir.glob("*.md")) if sources_dir.exists() else []
    src_context = ""
    for sf in src_files[:6]:  # die wichtigsten 6 Docs
        try:
            src_context += f"\n--- {sf.name} ---\n{sf.read_text(encoding='utf-8')[:2500]}\n"
        except Exception:
            pass

    report_text = strip_html(report_path.read_text(encoding="utf-8"))[:4000]

    prompt = f"""Du bist der FINAL FACT-CHECKER der Strategy-Pipeline.
Lies den gesamten Report durch und cross-checke JEDEN Fakt gegen die
Quell-Dokumente. Du bist die zweite, unabhängige Instanz (Lauras Prinzip:
'mach wie laura, nie wie ich') — finde was automatische Pattern-Checks
übersehen haben.

=== REPORT (vollständig) ===
{report_text[:9000]}

=== FACTS (Ground-Truth, Entity-Ground-Truth) ===
{json.dumps(facts.get('entities', {}), ensure_ascii=False, indent=1)[:2500]}

=== QUELL-DOKUMENTE (Auszüge) ===
{src_context[:6000]}

PRÜFE GENAU:
1. Jede Person die als 'Anzeige gegen X' / Anzeigenerstatter / 'erstattete'
   beschrieben wird — steht sie in facts.entities mit anzeigebereit=true?
   (Wenn anzeigebereit=false: HARD KONFLIKT)
2. Jede Zahl / Datum / Aktenzeichen im Report — steht sie so in den Quellen?
3. Jede Behauptung über eine Person (Rolle, Status) — widerspricht sie der Quelle?
4. Framework-Namen (Gabor/Sun Tzu/Sun Mate/OODA/Game Theory/Systems) im Report?
5. 'Linsen' / Testfall-Name (Laura) im Report?

ANTWORTE strikt im Format (eine Zeile pro Fund):
KONFLIKT: <Behauptung im Report> | <Was die Quelle sagt> | <Quellen-Ref>
Wenn kein Konflikt gefunden: schreibe genau eine Zeile: SAUBER"""

    try:
        # Hermes wirft am Ende a asyncio "Event loop is closed" RuntimeError
        # die durch subprocess.run durchbricht. Deshalb: Shell-Pipe mit
        # Datei-Redirect — des Parent-subprocess exited sauber (rc=0),
        # der asyncio-Error passiert nur im Child (Exception ignored).
        out_file = pathlib.Path(tempfile.mktemp(suffix=".txt"))
        cmd = f'hermes chat -q {shlex.quote(prompt)} -Q --skills final-factcheck > {out_file} 2>/dev/null'
        result = subprocess.run(cmd, shell=True, timeout=180)
        out = out_file.read_text(encoding="utf-8", errors="ignore")
        out_file.unlink(missing_ok=True)
        if not out.strip() and result.returncode != 0:
            return [f"WARN: LLM-Check Fehler (rc={result.returncode}). "
                    f"Pattern-Check läuft weiter."]
    except Exception as e:
        return [f"WARN: LLM-Check nicht ausführbar ({e}). Pattern-Check läuft weiter."]

    errors = []
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("KONFLIKT:"):
            errors.append(f"HARD FAIL [LLM]: {s}")
        elif s == "SAUBER":
            pass  # OK
    return errors


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 final-factcheck.py <report.html> <facts.json> [--sources dir] [--mode pattern|llm]")
        sys.exit(2)

    report_path = pathlib.Path(sys.argv[1])
    facts_path = pathlib.Path(sys.argv[2])
    mode = "pattern"
    sources_dir = report_path.parent
    if "--mode" in sys.argv:
        mode = sys.argv[sys.argv.index("--mode") + 1]
    if "--sources" in sys.argv:
        sources_dir = pathlib.Path(sys.argv[sys.argv.index("--sources") + 1])

    html = report_path.read_text(encoding="utf-8")
    text = strip_html(html)
    facts = json.loads(facts_path.read_text(encoding="utf-8"))

    print(f"=== Final Fact-Check ({mode}) ===")
    errors = pattern_check(text, facts)

    if mode == "llm" and "--no-llm" not in sys.argv:
        errors += llm_check(report_path, sources_dir, facts)

    if errors:
        print(f"KONFLIKTE GEFUNDEN ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
        print("\nGATE: BLOCKIERT — Endreport wird NICHT ausgeliefert.")
        sys.exit(1)
    else:
        print("✓ Final Fact-Check bestanden. Endreport darf raus.")
        sys.exit(0)


if __name__ == "__main__":
    main()
