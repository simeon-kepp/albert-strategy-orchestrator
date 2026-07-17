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
    """Delegiert an Subagent für kontextuellen Deep-Check.

    Der Subagent bekommt: (a) voller Report-Text, (b) facts.json,
    (c) Hinweis auf Quell-Docs. Er retourniert eine Liste von
    Konflikten im Format: 'KONFLIKT: <Behauptung> vs <Quelle>'.
    """
    # Hinweis: in echt ruft des delegate_task. Hier simulieren wir den
    # Trigger-Aufruf und parsen das Subagent-Resultat.
    prompt = f"""Du bist der FINAL FACT-CHECKER der Strategy-Pipeline.
Lies den gesamten Report durch und cross-checke JEDEN Fakt gegen die
Quell-Dokumente.

REPORT: {report_path.read_text(encoding='utf-8')[:8000]}...

FACTS (Ground-Truth): {json.dumps(facts, ensure_ascii=False)[:2000]}

QUELL-DOKUMENTE liegen in: {sources_dir}
- 02_TIEFENANALYSE: wer hat Anzeige erstattet (§6 Entity-Table!)
- 03_BEWEISLAGE: Anzeigenerstatterinnen-Liste

PRÜFE GENAU:
1. Jede Person die als 'Anzeige gegen X' / Anzeigenerstatter beschrieben
   wird — steht sie in facts.json mit anzeigebereit=true?
2. Jede Zahl/Datum/Aktenzeichen im Report — steht sie so in den Quellen?
3. Jede Behauptung über eine Person — widerspricht sie der Quelle?

RETURN: Eine Liste, eine Zeile pro Konflikt:
KONFLIKT: <Behauptung im Report> | <Was die Quelle sagt> | <Quellen-Ref>
Wenn kein Konflikt: 'SAUBER'."""

    # Trigger Subagent (Hermes delegate_task)
    try:
        result = subprocess.run(
            ["hermes", "delegate", "--goal", prompt, "--role", "leaf"],
            capture_output=True, text=True, timeout=120,
        )
        out = result.stdout
    except Exception as e:
        return [f"WARN: LLM-Check nicht ausführbar ({e}). Pattern-Check läuft weiter."]

    errors = []
    for line in out.splitlines():
        if line.strip().startswith("KONFLIKT:"):
            errors.append(f"HARD FAIL [LLM]: {line.strip()}")
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
