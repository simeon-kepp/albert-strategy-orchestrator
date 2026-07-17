#!/usr/bin/env python3
"""
fact-audit.py — Härte-Gate für die Strategy-Pipeline.

Prüft einen Report-Text (HTML) gegen eine Entity-Ground-Truth (facts.json).
Verhindert Fakt-Fehler wie den Sonia-Vorfall (fälschlich als Anzeigenerstatterin
deklariert).

Exit-Code 0 = OK (weiter zum Render).
Exit-Code 1 = HARD FAIL (Lauf bricht ab, KEIN PDF wird erzeugt).

Usage:
  python3 fact-audit.py <report.html> <facts.json>
"""
import sys
import json
import pathlib
import re

# Framework-Namen die NIE im Report stehen dürfen
FORBIDDEN_FRAMEWORKS = [
    "Gabor Maté", "Gabor Mate", "Sun Tzu", "Sun Mate",
    "OODA", "Game Theory", "Systems Thinking",
]
FORBIDDEN_BRANDS = ["Linsen", "Laura-Pipeline", "Laura's"]

# Verben die eine Anzeige implizieren
ANZEIGE_VERBS = [
    "anzeige gegen", "anzeige erstattet", "erstattete anzeige",
    "zeigte an", "klagte", "anzeigenerstatter", "anzeigebereit",
    "straft anzeige", "anzeige zum nachteil",
]


def strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def audit(html_path: pathlib.Path, facts_path: pathlib.Path) -> int:
    html = html_path.read_text(encoding="utf-8")
    text = strip_html(html)
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    entities = facts.get("entities", {})

    errors = []
    warnings = []

    # 1) Anzeige-Bereitschaft prüfen
    for name, meta in entities.items():
        bereit = meta.get("anzeigebereit", False)
        if not bereit:
            # Darf NIE mit Anzeige-Verb auftreten
            for verb in ANZEIGE_VERBS:
                if verb in text.lower() and name.split()[0].lower() in text.lower():
                    # Prüfe Kontext: steht der Name in der Nähe eines Anzeige-Verbs?
                    idx = text.lower().find(name.split()[0].lower())
                    if idx >= 0 and any(
                        verb in text.lower()[max(0,idx-40):idx+len(name)+40]
                        for verb in ANZEIGE_VERBS
                    ):
                        errors.append(
                            f"HARD FAIL: '{name}' (anzeigebereit=false) erscheint mit "
                            f"Anzeige-Verb. Quelle: {meta.get('quelle','?')}"
                        )

    # 2) Quellen-Pflicht (nur WARN, nicht HARD)
    for name, meta in entities.items():
        if name.lower() in text.lower():
            quelle = meta.get("quelle", "")
            # Extrahiere IMG_/Aktenzeichen aus Quelle
            refs = re.findall(r"(IMG_\d+|Az\.\s*[\w\s/]+|\d{3}\s*Js\s*\d+/\d+)", quelle)
            if refs:
                found = any(r.replace(" ", "") in text.replace(" ", "") for r in refs)
                if not found:
                    warnings.append(
                        f"WARN: '{name}' erwähnt, aber Quellen-Ref {refs[0]} fehlt im Text."
                    )

    # 3) Framework-Namen
    for fw in FORBIDDEN_FRAMEWORKS:
        if fw.lower() in text.lower():
            errors.append(f"HARD FAIL: Framework-Name '{fw}' im Report.")

    # 4) Brand-Namen
    for br in FORBIDDEN_BRANDS:
        if br.lower() in text.lower():
            errors.append(f"HARD FAIL: Brand/Personen-Marke '{br}' im Report.")

    # Report
    print(f"=== Fact-Audit: {html_path.name} ===")
    if warnings:
        print(f"Warnungen ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")
    if errors:
        print(f"FEHLER ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
        print("\nLauf ABGEBROCHEN — kein PDF erzeugt.")
        return 1
    else:
        print("✓ Alle Fakten verifiziert. Weiter zum Render.")
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 fact-audit.py <report.html> <facts.json>")
        sys.exit(2)
    rc = audit(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
    sys.exit(rc)
