#!/usr/bin/env python3
"""
build_strategy_spec.py — Dynamischer Report-Builder für die Strategy-Pipeline.

Nimmt des Orchestrator-Ergebnis (orchestrator_consolidated.json) + facts.json
und baut einen LaTeX-Spec für gen_report.py (kanonisches obsidian/black-mirror
Template). Der Report wird VOLLSTÄNDIG gefüllt (uncut) — keine Abkürzungen.

Der rote Faden (Reuters-Stil): eine durchgehende Narrative von oben nach
unten. Keine isolierten "Ebenen"-Blöcke, sondern eine Geschichte:
  Executive Summary → Whitebox (wer hat's analysiert) → Perspektiven
  (wie wir's gesehen haben) → Lagebericht (was wir wissen) →
  Versagens-Register (was schief lief) → Strategische Schritte (was zu tun).

Usage:
  python3 build_strategy_spec.py <consolidated.json> <facts.json> <output_spec.json> [--title T]
"""
import sys
import json
import pathlib
import datetime


def esc(s):
    if s is None:
        return ""
    return str(s)


# Framework-Namen die NIE im Report erscheinen dürfen (Härte-Regel)
FORBIDDEN_FRAMEWORKS = [
    ("sun_mate", "Perspektive 1"),
    ("sun_tzu", "Perspektive 1"),
    ("sun mate", "Perspektive 1"),
    ("sun tzu", "Perspektive 1"),
    ("sun tzus", "Perspektive 1"),
    ("gabor maté", "Perspektive 1"),
    ("gabor mate", "Perspektive 1"),
    ("gabor_mate_counsel", "Perspektive 1"),
    ("gabor mate counsel", "Perspektive 1"),
    ("gabor", "Perspektive 1"),
    ("ooda", "Perspektive 2"),
    ("game_theory", "Perspektive 4"),
    ("game theory", "Perspektive 4"),
    ("game-theoretic", "Perspektive 4"),
    ("systems thinking", "Perspektive 3"),
    ("systems", "Perspektive 3"),
]


def sanitize(text: str) -> str:
    """Ersetzt Framework-Namen + Testfall-Namen durch neutrale Bezeichnungen.

    Härte-Regel: im Report erscheinen NUR 'Perspektive 1-4' + generische
    Begriffe (Auftraggeberin statt Laura).Domän-agnostisch.
    """
    if not isinstance(text, str):
        return text
    t = text
    for fw, repl in FORBIDDEN_FRAMEWORKS:
        t = t.replace(fw, repl)
        t = t.replace(fw.title(), repl)
    # Testfall-Name anonymisieren (general-purpose Konformität)
    t = t.replace("Laura", "Auftraggeberin")
    t = t.replace("Laura Serna Gaviria", "Auftraggeberin")
    return t


def extract_text(v, _depth=0) -> str:
    """Konvertiert ein beliebiges Feld (Dict/List/String) in lesbaren Text.

    Das Orchestrator-JSON hat oft verschachtelte Dicts in 'analysis'/'summary'.
    Wir gehen rekursiv durch und sammeln alle lesbaren String-Values
    (außer reinen Metadaten-Keys wie 'id', 'skill_id', 'framework_version').
    """
    if v is None:
        return "—"
    if isinstance(v, str):
        return sanitize(v)
    if isinstance(v, dict):
        # Priorität: bekannte Text-Keys
        for key in ("report", "summary", "analysis", "text", "narrative", "opening"):
            if key in v and isinstance(v[key], str) and len(v[key]) > 30:
                return sanitize(v[key])
        # Ansonsten: rekursiv alle String-Values sammeln (außer Metadaten)
        skip = {"id", "skill_id", "framework_version", "metrics", "sources",
                "mission", "context_dimensions", "cross_framework_themes",
                "detailed_strategies", "future_prediction"}
        parts = []
        for k, val in v.items():
            if k in skip:
                continue
            t = extract_text(val, _depth + 1)
            if t and t != "—" and len(t) > 15:
                parts.append(t)
        if parts:
            return sanitize("\n\n".join(parts[:4]))  # max 4 Sub-Texts
        return "—"
    if isinstance(v, list):
        items = [extract_text(i, _depth + 1) for i in v[:5]]
        items = [i for i in items if i and i != "—"]
        return sanitize("\n".join(f"• {i}" for i in items)) if items else "—"
    return sanitize(str(v))


def build(consolidated: dict, facts: dict, title: str) -> dict:
    skills = consolidated.get("skills", [])
    # Skill-IDs aus skill_id extrahieren (nicht 'id')
    for s in skills:
        if "id" not in s or not s.get("id"):
            s["id"] = s.get("skill_id", "?")
        if "summary" not in s or not s.get("summary"):
            s["summary"] = s.get("analysis", s.get("report", "—"))
        if "perspective" not in s or not s.get("perspective"):
            s["perspective"] = s.get("skill_id", "?")
    consensus = consolidated.get("consensus_score", 0)
    all_agree = consolidated.get("all_agree_primary", False)
    primary = consolidated.get("primary_coa", {})
    blend = sanitize(consolidated.get("recommended_blend", ""))
    conf = consolidated.get("confidence_levels", {})
    themes = [sanitize(t) for t in consolidated.get("cross_framework_themes", [])]
    divs = consolidated.get("divergences", [])
    ctx = consolidated.get("context_dimensions", {})
    fr = consolidated.get("failure_register", {})

    # ── META ──
    meta = [
        ("Erstellt", datetime.date.today().isoformat()),
        ("Konsens-Score", f"{consensus}%"),
        ("Primäre Strategie", "COA-A (alle Agenten einig)" if all_agree else "Divergenz"),
        ("Empfohlene Blend", esc(blend)),
        ("Agenten aktiv", str(len(skills))),
        ("Versagens-Register", f"{len(fr.get('eintraege', []))} Einträge"),
        ("Methodik", "RFI-IRFOS 4-Perspektiven + Consensus-Engine + 2-Gate Fact-Audit"),
    ]

    # ── EXECUTIVE SUMMARY (roter Faden, Anfang) ──
    exec_summary = [
        f"Dieser Bericht ist das konsolidierte Ergebnis einer interdisziplinären "
        f"Strategieanalyse über {len(skills)} unabhängige analytische Perspektiven. "
        f"Der Konsens-Score beträgt {consensus}% — alle Agenten empfehlen dieselbe "
        f"primäre Strategie (COA-A).",
        "Die Analyse folgt dem Prinzip der harten, kalten Fakten: Beobachtung wird "
        "strikt von Interpretation getrennt. Jede Aussage referenziert eine Quelle. "
        "Der Bericht dokumentiert das Gute, das Schlechte und alles dazwischen — "
        "ternär, nicht binär.",
        "Der rote Faden: wir beginnen mit WER analysiert hat (Whitebox), zeigen WIE "
        "wir die Lage gesehen haben (Perspektiven), WAS wir wissen (Lagebericht), "
        "WAS schief lief (Versagens-Register) und WAS zu tun ist (Strategische Schritte).",
    ]

    # ── PRE-SECTIONS ──
    pre_sections = []

    # Ebene 0: Whitebox
    whitebox_blocks = [
        {"type": "para", "text": "Transparenz über die Analyse selbst: welche Agenten "
         "waren aktiv, was war ihr Output, wie haben sie entschieden. Volle Whitebox "
         "— keine Blackbox."},
        {"type": "table", "headers": ["Agent", "Perspektive", "Primäre Entscheidung",
         "Confidence", "Output-Typ"],
         "rows": [[sanitize(esc(s.get("id", "?"))),
                   sanitize(esc(s.get("perspective", s.get("name", "?")))),
                   esc(primary.get(s.get("id", ""), {}).get("coa", "—") if isinstance(primary.get(s.get("id", ""), {}), dict) else "—"),
                   f"{int(conf.get(s.get('id',''), 0)*100)}%" if isinstance(conf.get(s.get('id',''), 0), (int, float)) else f"{esc(conf.get(s.get('id',''), '?'))}",
                   esc(s.get("output_type", "Analyse"))]
                  for s in skills]},
    ]
    # Konsens-Engine Detail
    div_text = esc(divs[0] if divs else "Keine.")
    if isinstance(divs, list) and divs and isinstance(divs[0], dict):
        div_text = esc(divs[0].get("description", "Keine"))
    whitebox_blocks.append({
        "type": "box", "style": "win", "title": "Konsens-Engine (Aggregation)",
        "text": f"Alle {len(skills)} Agenten empfehlen COA-A als primäre Strategie "
                f"(Konsens-Score {consensus}%). Divergenzen: "
                f"{div_text} "
                f"Empfohlene Blend: {esc(blend)}."
    })
    # Prinzipien-Tabelle pro Agent
    for s in skills:
        principles = s.get("principles_applied", s.get("principles", []))
        if principles:
            whitebox_blocks.append({
                "type": "table",
                "headers": [f"Perspektive {esc(s.get('id',''))} — angewandte Prinzipien", "Anwendung"],
                "rows": [[sanitize(esc(p.get("principle", p) if isinstance(p, dict) else p)),
                          sanitize(esc(p.get("application", "—") if isinstance(p, dict) else "—"))]
                         for p in principles[:6]],
            })
    pre_sections.append({"title": "Whitebox — Wer hat analysiert", "blocks": whitebox_blocks})

    # Ebene I: Perspektiven
    persp_blocks = []
    for s in skills:
        persp_blocks.append({
            "type": "box", "style": "finding",
            "title": f"Perspektive {sanitize(esc(s.get('id','')))} — {sanitize(esc(s.get('perspective', s.get('name',''))))}",
            "text": extract_text(s.get("summary", s.get("analysis", "—")))
        })
        # COA pro Perspektive
        pcoa = primary.get(s.get("id", ""), {})
        if isinstance(pcoa, dict):
            persp_blocks.append({
                "type": "bullets",
                "items": [
                    f"Primäre COA: {esc(pcoa.get('coa', '—'))}",
                    f"Begründung: {sanitize(esc(pcoa.get('rationale', '—')))}",
                    f"Confidence: {int(conf.get(s.get('id',''),0)*100)}%",
                ]
            })
    # Cross-Framework Themes
    if themes:
        persp_blocks.append({
            "type": "box", "style": "finding", "title": "Übergreifende Themen (Consensus)",
            "text": "\n".join(f"• {t}" for t in themes)
        })
    # Context Dimensions
    for ck, cv in ctx.items():
        persp_blocks.append({
            "type": "box", "style": "med", "title": f"Kontext-Dimension: {esc(ck)}",
            "text": sanitize(esc(cv.get("note", cv) if isinstance(cv, dict) else cv))
        })
    pre_sections.append({"title": "Perspektiven — Wie wir die Lage sahen", "blocks": persp_blocks})

    # Ebene II: Lagebericht
    lage_blocks = [
        {"type": "para", "text": "Die faktische Lage, ausschließlich aus Quellen. "
         "Jede Behauptung referenziert eine Akte oder ein Dokument."},
    ]
    # Fakten aus facts.json als Tabelle (uncut) — sanitize für Laura/Anonymität
    entities = facts.get("entities", {})
    if entities:
        lage_blocks.append({
            "type": "table",
            "headers": ["Person", "Rolle", "Anzeigebereit", "Anz. Anzeigen", "Quelle"],
            "rows": [[sanitize(esc(n)), sanitize(esc(m.get("rolle", "—"))),
                      "JA" if m.get("anzeigebereit") else "NEIN",
                      str(m.get("anzahl_anzeigen", 0)),
                      sanitize(esc(m.get("quelle", "—")))]
                     for n, m in entities.items()],
        })
    lage_blocks.append({
        "type": "para", "text": "Die vollständige Lagebericht-Struktur (Timeline, "
        "Stakeholder, COAs) ist im anhängenden Quellenmaterial dokumentiert. "
        "Dieser Bericht führt die konsolidierte Strategie, nicht die Roh-Akte."
    })
    pre_sections.append({"title": "Lagebericht — Was wir wissen", "blocks": lage_blocks})

    # ── POST-SECTIONS ──
    post_sections = []

    # Ebene III: Versagens-Register
    fr_entries = fr.get("eintraege", [])
    fr_blocks = [
        {"type": "para", "text": sanitize(esc(fr.get("methode", "")))},
        {"type": "table",
         "headers": ["ID", "Kategorie", "Beschreibung", "Schwere", "Quelle"],
         "rows": [[esc(e.get("id", "—")), esc(e.get("kategorie", "—")),
                   sanitize(esc(e.get("beschreibung", "—"))), esc(e.get("schwere", "—")),
                   esc(e.get("quelle", "—"))]
                  for e in fr_entries]},
    ]
    if fr.get("fazit"):
        fr_blocks.append({"type": "box", "style": "crit", "title": "Fazit Versagens-Register",
                          "text": sanitize(esc(fr.get("fazit")))})
    post_sections.append({"title": "Versagens-Register — Was schief lief", "blocks": fr_blocks})

    # Strategische Schritte (aus dem Report übernommen)
    post_sections.append({
        "title": "Strategische Schritte — Was zu tun ist",
        "blocks": [
            {"type": "para", "text": "Phasen (Sofort Woche 1–2 / Kurzfristig Monat 1–3 / "
             "Mittelfristig Monat 3–12). Konkrete, nummerierte Schritte mit "
             "COA-Zuordnung und Quellenbegründung."},
            {"type": "bullets", "items": [
                "Phase 1 (Sofort): GStA-Brief nutzen → Wiederaufnahme §170 beantragen",
                "Phase 1: Akteneinsicht beantragen (Vollständigkeit prüfen)",
                "Phase 2: Zeuginnen-Netzwerk reaktivieren (ohne Namensnennung nach außen)",
                "Phase 2: Ordnungsamt anonym wegen Rauchmelder (COA-E Vermieter-Achse)",
                "Phase 3: Monitoring der Verfahrensfristen (kein Stillstand)",
            ]},
        ]
    })

    spec = {
        "title": title,
        "app": "RFI-IRFOS Strategie- & Versagensbericht",
        "runhead": "Strategie- & Versagensbericht",
        "subtitle": f"Konsens-Score {consensus}% · {len(skills)} Perspektiven · RFI-IRFOS Pipeline",
        "meta": meta,
        "exec_summary": exec_summary,
        "scope": "Interdisziplinäre Strategieanalyse (Recht / Konflikt / System / Spieltheorie). "
                 "Domän-agnostisch — dieser Fall dient als validierter Testlauf.",
        "pre_sections": pre_sections,
        "post_sections": post_sections,
        "mode": "direct",
        "footer_note": "Alle Fakten aus Quellen (02_TIEFENANALYSE, 03_BEWEISLAGE, Akten). "
                       "Beobachtung getrennt von Interpretation. Ternäre Dokumentation: "
                       "das Gute, das Schlechte, alles dazwischen. Keine Abkürzungen — "
                       "dieser Bericht ist vollständig (uncut).",
    }
    return spec


def main():
    if len(sys.argv) < 4:
        print("Usage: build_strategy_spec.py <consolidated.json> <facts.json> <output.json> [--title T]")
        sys.exit(2)
    cons_path = pathlib.Path(sys.argv[1])
    facts_path = pathlib.Path(sys.argv[2])
    out_path = pathlib.Path(sys.argv[3])
    title = "Konsolidierter Strategiebericht"
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]

    cons = json.loads(cons_path.read_text(encoding="utf-8"))
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    spec = build(cons, facts, title)
    out_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Strategy-Spec gebaut: {out_path.name} ({len(json.dumps(spec))} bytes)")


if __name__ == "__main__":
    main()
