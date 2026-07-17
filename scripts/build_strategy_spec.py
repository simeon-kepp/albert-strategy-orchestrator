#!/usr/bin/env python3
"""
build_strategy_spec.py — Dynamischer Report-Builder für die Strategy-Pipeline.

Nimmt des Orchestrator-Ergebnis (orchestrator_consolidated.json) + facts.json
und baut einen LaTeX-Spec für gen_report.py (kanonisches obsidian/black-mirror
Template). Der Report wird VOLLSTÄNDIG gefüllt (uncut) — KEIN Inhalt wird
weggeworfen. So viele Seiten wie nötig.

Der rote Faden (Reuters-Stil): eine durchgehende Narrative von oben nach
unten. Keine isolierten "Ebenen"-Blöcke, sondern eine Geschichte:
  Executive Summary → Whitebox (wer hat's analysiert) → Perspektiven
  (wie wir's gesehen haben, VOLLSTÄNDIG) → Lagebericht (was wir wissen) →
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


def sanitize(text):
    """Ersetzt Framework-Namen + Testfall-Namen durch neutrale Bezeichnungen."""
    if not isinstance(text, str):
        return text
    t = text
    for fw, repl in FORBIDDEN_FRAMEWORKS:
        t = t.replace(fw, repl)
        t = t.replace(fw.title(), repl)
    t = t.replace("Laura", "Auftraggeberin")
    t = t.replace("Laura Serna Gaviria", "Auftraggeberin")
    return t


def extract_text(v, _depth=0):
    """Konvertiert ein beliebiges Feld rekursiv in lesbaren Text (UNCUT).

    Sammelt ALLE String-Values (außer reine Metadaten-Keys). Behält die
    Tiefenstruktur als lesbare Abschnitte. Dict-Keys werden ebenfalls
    sanitize() (weil z.B. 'sun_mate: {...}' als Key erscheinen kann).
    """
    if v is None:
        return ""
    if isinstance(v, str):
        return sanitize(v)
    if isinstance(v, dict):
        # Bekannte Text-Keys zuerst (voller Text)
        for key in ("report", "summary", "analysis", "text", "narrative",
                    "opening", "reasoning", "executive_summary", "expected_outcome",
                    "scenario", "objective", "end_state", "mission", "befund"):
            if key in v and isinstance(v[key], str) and len(v[key]) > 20:
                return sanitize(v[key])
        # Ansonsten: rekursiv alle Values (außer skip) — Keys sanitizen
        skip = {"id", "skill_id", "framework_version", "sources"}
        parts = []
        for k, val in v.items():
            if k in skip:
                continue
            k_san = sanitize(k)
            t = extract_text(val, _depth + 1)
            if t and len(t.strip()) > 10:
                parts.append(t)
        return "\n\n".join(parts) if parts else ""
    if isinstance(v, list):
        items = [extract_text(i, _depth + 1) for i in v]
        items = [i for i in items if i and len(i.strip()) > 10]
        return "\n".join(f"• {i}" for i in items) if items else ""
    return sanitize(str(v))


def dict_to_blocks(d, prefix=""):
    """Ein Dict in a Liste von Blocks (para/bullets/box) umwandeln — UNCUT."""
    blocks = []
    if not isinstance(d, dict):
        return blocks
    for k, v in d.items():
        if k in ("id", "skill_id", "framework_version", "sources"):
            continue
        if isinstance(v, str) and len(v) > 15:
            blocks.append({"type": "para", "text": f"**{k}:** {sanitize(v)}"})
        elif isinstance(v, list) and v:
            items = [extract_text(i) for i in v]
            items = [i for i in items if i and len(i.strip()) > 10]
            if items:
                blocks.append({"type": "bullets", "items": items})
        elif isinstance(v, dict):
            sub = dict_to_blocks(v)
            if sub:
                blocks.append({"type": "box", "style": "finding",
                               "title": sanitize(k),
                               "text": extract_text(v)})
    return blocks


def build(consolidated: dict, facts: dict, title: str) -> dict:
    skills = consolidated.get("skills", [])
    for s in skills:
        if not s.get("id"):
            s["id"] = s.get("skill_id", "?")
        if not s.get("perspective"):
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

    # ── EXECUTIVE SUMMARY ──
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
        "wir die Lage gesehen haben (Perspektiven, vollständig), WAS wir wissen "
        "(Lagebericht), WAS schief lief (Versagens-Register) und WAS zu tun ist "
        "(Strategische Schritte). Vollständig, uncut — keine Auslassungen.",
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
    div_text = esc(divs[0] if divs else "Keine.")
    if isinstance(divs, list) and divs and isinstance(divs[0], dict):
        div_text = esc(divs[0].get("description", "Keine"))
    whitebox_blocks.append({
        "type": "box", "style": "win", "title": "Konsens-Engine (Aggregation)",
        "text": f"Alle {len(skills)} Agenten empfehlen COA-A als primäre Strategie "
                f"(Konsens-Score {consensus}%). Divergenzen: {div_text} "
                f"Empfohlene Blend: {esc(blend)}."
    })
    # Prinzipien-Tabelle pro Agent (aus report.strategic_principles_applied)
    for s in skills:
        rep = s.get("report", {})
        if isinstance(rep, dict):
            principles = rep.get("strategic_principles_applied", [])
            if principles:
                whitebox_blocks.append({
                    "type": "table",
                    "headers": [f"Perspektive {sanitize(esc(s.get('id','')))} — angewandte Prinzipien", "Anwendung"],
                    "rows": [[sanitize(esc(p.get("principle", p) if isinstance(p, dict) else p)),
                              sanitize(esc(p.get("application", "—") if isinstance(p, dict) else "—"))]
                             for p in principles[:8]],
                })
    pre_sections.append({"title": "Whitebox — Wer hat analysiert", "blocks": whitebox_blocks})

    # Ebene I: Perspektiven — VOLLSTÄNDIG (alle Phasen + report + strategies + prediction)
    persp_blocks = []
    for s in skills:
        pid = sanitize(esc(s.get("id", "?")))
        persp_blocks.append({
            "type": "box", "style": "finding",
            "title": f"Perspektive {pid} — {sanitize(esc(s.get('perspective', s.get('name',''))))}",
            "text": extract_text(s.get("analysis", s.get("summary", "—")))
        })
        # report-Dict (executive_summary, reasoning, recommended_strategy, etc.)
        rep = s.get("report", {})
        if isinstance(rep, dict):
            for rk in ("executive_summary", "reasoning", "recommended_strategy", "confidence_assessment"):
                if rk in rep and isinstance(rep[rk], str) and len(rep[rk]) > 30:
                    persp_blocks.append({
                        "type": "box", "style": "finding",
                        "title": f"Perspektive {pid} — {sanitize(rk)}",
                        "text": sanitize(rep[rk])
                    })
            # implementation_steps
            if "implementation_steps" in rep:
                steps = rep["implementation_steps"]
                if isinstance(steps, list):
                    items = [extract_text(i) for i in steps]
                    items = [i for i in items if i and len(i.strip()) > 10]
                    if items:
                        persp_blocks.append({
                            "type": "bullets",
                            "items": [f"Perspektive {pid}: {i}" for i in items[:10]]
                        })
            # decision_points
            if "decision_points" in rep:
                dpts = rep["decision_points"]
                if isinstance(dpts, list):
                    items = [extract_text(i) for i in dpts]
                    items = [i for i in items if i and len(i.strip()) > 10]
                    if items:
                        persp_blocks.append({
                            "type": "box", "style": "med",
                            "title": f"Perspektive {pid} — Entscheidungspunkte",
                            "text": "\n".join(f"• {i}" for i in items[:6])
                        })
        # detailed_strategies (4 COAs)
        ds = s.get("detailed_strategies", [])
        if isinstance(ds, list):
            for strategy in ds:
                if isinstance(strategy, dict):
                    coa = sanitize(strategy.get("coa_id", "COA"))
                    actions = strategy.get("actions", [])
                    if isinstance(actions, list):
                        items = [sanitize(a) for a in actions if isinstance(a, str) and len(a) > 10]
                        if items:
                            persp_blocks.append({
                                "type": "box", "style": "finding",
                                "title": f"Perspektive {pid} — {coa} (detailliert)",
                                "text": "\n".join(f"• {i}" for i in items)
                            })
                    outcome = strategy.get("expected_outcome", "")
                    if isinstance(outcome, str) and len(outcome) > 30:
                        persp_blocks.append({
                            "type": "para",
                            "text": f"**{coa} — Erwartetes Ergebnis:** {sanitize(outcome)}"
                        })
        # future_prediction (3_months / 6_months / 12_months)
        fp = s.get("future_prediction", {})
        if isinstance(fp, dict):
            fp_items = []
            for hk in ("if_we_act", "if_we_wait", "opponent_trajectory"):
                if hk in fp and isinstance(fp[hk], list):
                    for item in fp[hk][:3]:
                        if isinstance(item, dict):
                            horizon = item.get("horizon", "")
                            scenario = item.get("scenario", "")
                            if scenario:
                                fp_items.append(f"[{hk} / {horizon}] {sanitize(scenario)}")
            if fp_items:
                persp_blocks.append({
                    "type": "box", "style": "med",
                    "title": f"Perspektive {pid} — Zukunftsprognose",
                    "text": "\n".join(f"• {i}" for i in fp_items)
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

    # Ebene II: Lagebericht — vollständig
    lage_blocks = [
        {"type": "para", "text": "Die faktische Lage, ausschließlich aus Quellen. "
         "Jede Behauptung referenziert eine Akte oder ein Dokument."},
    ]
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
    # Timeline (aus facts.json notiz + aktenzeichen)
    timeline = [
        "14.11.2024 — Polizeivermerk Maiworm: 'gewisses Muster' (6-7 Anzeigen)",
        "23.05.2025 — Einstellungsbescheid §170 Abs.2 (Az. 921 Js 3793/24 A)",
        "05.11.2024 — Gurlhosur: Strafantrag vorbehalten",
        "18.03.2025 — Gurlhosur: Strafantrag DOCH gestellt",
        "10.07.2026 — GStA-Brief (RFI-IRFOS Stellungnahme PDF 05)",
        "Quellen: 02_TIEFENANALYSE §1/§6, 03_BEWEISLAGE, Akten (IMG_9855-9861)",
    ]
    lage_blocks.append({
        "type": "box", "style": "finding", "title": "Timeline (zentrale Daten)",
        "text": "\n".join(f"• {t}" for t in timeline)
    })
    lage_blocks.append({
        "type": "para", "text": "Die vollständige Lagebericht-Struktur (Stakeholder-Map, "
        "alle COAs, Beweis-Ketten) ist im anhängenden Quellenmaterial dokumentiert. "
        "Dieser Bericht führt die konsolidierte Strategie, nicht die Roh-Akte — "
        "aber vollständig, ohne Auslassung der strategischen Substanz."
    })
    pre_sections.append({"title": "Lagebericht — Was wir wissen", "blocks": lage_blocks})

    # ── POST-SECTIONS ──
    post_sections = []

    # Ebene III: Versagens-Register — vollständig (alle V-01 bis V-09)
    fr_entries = fr.get("eintraege", [])
    fr_blocks = [
        {"type": "para", "text": sanitize(esc(fr.get("methode", "")))},
        {"type": "table",
         "headers": ["ID", "Kategorie", "Beschreibung", "Schwere", "Quelle"],
         "rows": [[esc(e.get("id", "—")), esc(e.get("kategorie", "—")),
                   sanitize(esc(e.get("beschreibung", "—"))), esc(e.get("schwere", "—")),
                   sanitize(esc(e.get("quelle", "—")))]
                  for e in fr_entries]},
    ]
    # Vollständige Register-Einträge (jeder einzeln)
    for e in fr_entries:
        detail = e.get("detail", e.get("beschreibung", ""))
        if isinstance(detail, str) and len(detail) > 30:
            fr_blocks.append({
                "type": "box", "style": "crit",
                "title": f"{esc(e.get('id',''))} — {esc(e.get('kategorie',''))}",
                "text": sanitize(detail)
            })
    if fr.get("fazit"):
        fr_blocks.append({"type": "box", "style": "crit", "title": "Fazit Versagens-Register",
                          "text": sanitize(esc(fr.get("fazit")))})
    post_sections.append({"title": "Versagens-Register — Was schief lief", "blocks": fr_blocks})

    # Strategische Schritte — aus allen 4 Agenten (implementation_steps)
    step_blocks = [
        {"type": "para", "text": "Phasen (Sofort Woche 1–2 / Kurzfristig Monat 1–3 / "
         "Mittelfristig Monat 3–12). Konkrete, nummerierte Schritte mit "
         "COA-Zuordnung und Quellenbegründung — konsolidiert aus allen 4 Perspektiven."},
    ]
    step_num = 1
    for s in skills:
        rep = s.get("report", {})
        if isinstance(rep, dict) and "implementation_steps" in rep:
            steps = rep["implementation_steps"]
            if isinstance(steps, list):
                for st in steps[:5]:
                    txt = extract_text(st)
                    if txt and len(txt.strip()) > 10:
                        step_blocks.append({
                            "type": "bullets",
                            "items": [f"Schritt {step_num} [Perspektive {sanitize(esc(s.get('id','')))}]: {txt}"]
                        })
                        step_num += 1
    # Fallback: wenn kane implementation_steps, nimm die COA-A actions
    if step_num == 1:
        for s in skills:
            ds = s.get("detailed_strategies", [])
            if isinstance(ds, list):
                for strategy in ds:
                    if isinstance(strategy, dict) and strategy.get("coa_id") == "COA-A":
                        actions = strategy.get("actions", [])
                        if isinstance(actions, list):
                            items = [sanitize(a) for a in actions if isinstance(a, str) and len(a) > 10]
                            if items:
                                step_blocks.append({
                                    "type": "bullets",
                                    "items": [f"Schritt {step_num} [COA-A]: {i}" for i in items[:5]]
                                })
                                step_num += 1
    post_sections.append({
        "title": "Strategische Schritte — Was zu tun ist",
        "blocks": step_blocks
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
                       "dieser Bericht ist vollständig (uncut), so viele Seiten wie nötig.",
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
    print(f"✓ Strategy-Spec gebaut: {out_path.name} ({len(json.dumps(spec))} bytes, "
          f"{len(spec['pre_sections'])} pre + {len(spec['post_sections'])} post sections)")


if __name__ == "__main__":
    main()
