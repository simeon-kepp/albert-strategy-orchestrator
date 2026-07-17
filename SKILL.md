---
name: strategy-pipeline
description: "GENERAL-PURPOSE Strategie-Pipeline. Nimmt OBEN irgendeine Problemstellung (Prompt/Textdatei, beliebige Domäne) und läuft VOLLautomatisch durch: (1) 4 analytische Perspektiven (generisch, domän-agnostisch), (2) Consensus-Engine, (3) Strategiebericht, (4) interdisziplinäres Versagens-Register, (5) Peer-Review-Subagent, (6) finaler 1-PDF-Report mit DYNAMISCHER, kontext-aware Länge (kleiner Fall = wenige Seiten, großer = 50+; nie fix). WICHTIG: Die Framework-Namen (Sun Tzu, OODA, Game Theory, Systems, Gabor Maté, Sun Mate) erscheinen NIE im Report — die Perspektiven sind anonyme Werkzeuge ('Perspektive 1–4'). Läuft über den Rust-Orchestrator albert-strategy-orchestrator. Trigger: 'strategie pipeline', 'problemstellung analysiern', 'lauf die pipeline', 'generischer strategie-report', 'mach mir den bericht zu X'."
version: 1.0.0
author: Hermes Agent / RFI-IRFOS
license: MIT
metadata:
  hermes:
    tags: [strategy, pipeline, general-purpose, orchestrator, consensus, peer-review, dynamic-report, domän-agnostisch]
    related_skills: [sun-mate, ooda, systems, game-theory, strategy-orchestrator, failure-audit, context-audit]
---

# Strategy Pipeline (General-Purpose)

## Was es tut

Nimmt **irgendeine Problemstellung** (ein Prompt, eine Textdatei, ein Fall,
beliebige Domäne — Recht, Business, Konflikt, Organisationsentwicklung,
politische Strategie, Persönlichkes) und produziert **einen einzigen,
konsolidierten Strategie- & Versagensbericht** als PDF.

Die Pipeline ist **domän-agnostisch**. Sie isch NICHT auf den Laura-Testfall
spezialisiert — der diente nur zum Validiern. Jeder neue Prompt läuft
identisch durch.

## Die 4 analytischen Perspektiven (anonym, generisch)

Die Pipeline nutzt 4 unabhängige analytische Linsen. Im Report erscheinen
sie NIE namentlich — nur als **Perspektive 1–4** mit thematischer
Beschreibung. Sie sind Werkzeuge, keine Akteure.

Die 4 Perspektiven operieren nach diesen generischen Prinzipien
(die Rahmen sind domän-übergreifend):

- **Perspektive 1 — Strategische Klarheit & Hebel:** Wo ist der
  Hebelpunkt, der die Gesamtsituation verschiebt, ohne die eigene
  Partei zu exponieren? Der höchste Gewinn isch der ohne offenen
  Konflikt errungene.
- **Perspektive 2 — Entscheidungs-Tempo:** Wer orientiert und handelt
  schneller als der Gegner, diktiert die Agenda. Tempo + Ziel + Hebel =
  konsolidierte Bewegung. Aber: Überhastung produziert Eigenfehler.
- **Perspektive 3 — Systemstruktur & Rückkopplung:** Der Fall isch
  ein vernetztes System, nicht a Einzelfall. Wo sind die
  Rückkopplungsschleifen, die das Problem verstärken? Wo ist der
  Hebelpunkt außerhalb der offensichtlichen Arena?
- **Perspektive 4 — Strategische Interaktion & Gleichgewicht:** Der
  Fall isch a wiederholtes Spiel zwischen Akteuren. Was isch die
  dominante Strategie? Wo verschiebt sich das Gleichgewicht durch
  einen Koordinationspunkt?

Diese Prinzipien sind in den Skills `sun_mate`, `ooda`, `systems`,
`game_theory` konkretisiert (die Skills sind die Werkzeug-Kisten,
werden aber im Report ned genannt).

## Pipeline-Phasen

```
Phase 1: Problemstellung einnehmen (Prompt/Datei)
Phase 2: 4 Perspektiven analysieren (skills/strategy/<id>/analysis.json)
Phase 3: Consensus-Engine (albert-strategy-orchestrator)
Phase 4: Strategiebericht generiern
Phase 5: Versagens-Register (failure-audit Skill)
Phase 6: Peer-Review-Subagent (second pass, strengthening)
Phase 7: Finaler 1-PDF-Report (dynamische Länge)
```

## Verwendung

```bash
# Rust-Orchestrator (4 Skills konsolidiern)
cd /home/eri-irfos/projects/albert-strategy-orchestrator
cargo build
./target/debug/albert-strategy-orchestrator \
  --skills sun_mate,ooda,systems,game_theory \
  --mission <problemstellung.txt> \
  --out <konsolidated.json>

# Report-Rendering (dynamische Länge via Chrome + pdfunite)
# Siehe scripts/ im strategy-orchestrator Skill
```

## Dynamische, kontext-aware Länge

Der Report isch **nie fix lang**. Die Länge richtet sich nach der
Komplexität der Problemstellung:

- **Kleiner Fall** (einfache Entscheidung): ~3–5 Seiten.
- **Mittlerer Fall**: ~10–15 Seiten.
- **Großer Fall** (viele Akteure, viele Dokumente, viele Versagen):
  20–50+ Seiten.

Mechanik (im Renderer): Das HTML wird in Sektionen gesplittet
(Ebene 1/2/3 + Sub-Sektionen), jede Sektion einzeln mit Chrome
gerendert, dann mit `pdfunite` gemerged. `break-before: page` auf
`.divider` respektiert Chrome-headless zuverlässig pro separat
gerendertem Part (nicht im Gesamt-HTML — des isch a bekannter
Chrome-headless-Bug).

**WICHTIG:** Die Länge isch kontext-aware. Bei a klarer, kleiner
Problemstellung KEIN 50-Seiten-Report erzwingen. Bei a komplexen
Fall KEIN 8-Seiten-Report kappen. Die Substanz bestimmt die Länge.

## KEINE Framework-Namen im Report

Striker Grundsatz: Im finalen PDF erscheinen NIE: "Gabor Maté",
"Sun Tzu", "Sun Mate", "OODA", "Game Theory", "Systems Thinking",
oder ähnliches. Die Perspektiven sind anonyme Werkzeuge. Im
Peer-Review wird explizit auf Namens-Leakage geprüft.

Begründung: Die Analyse-Werkzeuge sind Werkzeuge. Ihre Identität isch
für die Lesbarkeit des Berichts irrelevant. Der Bericht soll als
direkter, neutraler Lagebericht stehen — "es isch einfach so".

## Peer-Review (Second Pass)

Nach dem ersten Draft wird a **Peer-Review-Subagent** (delegate_task,
leaf) drüberschaun mit genau diesen Prüfpunkten:

1. **Namens-Leakage:** Enthält der Report irgendwo Framework-Namen?
   (NEIN gefordert.)
2. **Seitenzahl:** Ist der Report substantiell genug für die
   Komplexität der Problemstellung? (Kontext-aware, nie zu kurz.)
3. **Fehlende Fakten:** Welche echten Belege/Details aus den
   Quelldokumenten fehlen noch und würden den Report stärken?
4. **Logik/Lücken:** Inkonsistenzen, fehlende Gegendarstellung,
   Struktur-Sprünge?

Der Peer-Review-Agent darf KEINE Dateien verändern — nur Feedback
geben. Die Haupt-Instanz baut des Feedback ein.

## Output-Struktur (1 PDF, 3 Ebenen)

```
EBENE 1 — Vier analytische Perspektiven (anonym, thematisch benennt)
EBENE 2 — Strategischer Lagebericht
  - Mission Scorecard
  - Courses of Action (A–E)
  - Risiko-Matrix
  - COA-Narrative (ausführlich)
  - Zentrale Evidenz (quellenbelegt)
  - Timeline
  - Stakeholder-Map
  - Future Prediction (3/6/12 Monate)
  - Detail-Anhänge
EBENE 3 — Interdisziplinäres Versagens-Register
  (jeder Eintrag: was schief lief, Gesetz, warum kritisch,
   Mitigation, Gegenseite, 3 Optionen)
```

## Integration mit anderen Skills

- `sun_mate`, `ooda`, `systems`, `game_theory`: Die 4 Werkzeug-Skills.
- `strategy-orchestrator`: Der Rust-Orchestrator-Wrapper.
- `failure-audit`: Das Versagens-Register (Ebene 3).
- `context-audit`: Findet übersehene Nuancen (Input für Ebene 2).

## Pitfalls

- **Chrome-headless `break-before` Bug:** Im Gesamt-HTML respektiert
  Chrome `break-before: page` nicht zuverlässig. Lösung: HTML in
  Sektionen splittn, jede einzeln rendern, mit `pdfunite` mergen.
- **Framework-Namen:** Strikt vermeiden im Report. Peer-Review prüft.
- **Dynamische Länge:** Nicht fix kappen. Substanz bestimmt Seitenzahl.
- **Domän-agnostisch bleiben:** Die Pipeline isch generisch. Laura war
  nur der Testfall. Jeder neue Prompt läuft identisch.
- **Peer-Review darf ned schreiben:** Nur Feedback, Haupt-Instanz baut ein.

## Beispiel (Testfall war Laura — generisch gemeint)

```
Input:  "Analyier mir den Konflikt zwischen Team A und Team B
          wegen Ressourcen-Allokation in unserer Firma."

Pipeline läuft:
  4 Perspektiven → Consensus → Strategiebericht →
  Versagens-Register → Peer-Review → 1 PDF (dyn. Länge)

Output: total_report.pdf (z.B. 12 Seiten für diesen Fall)
```

Die Domäne isch egal. Recht, Business, Politik, Persönlichkes —
die Pipeline isch domän-agnostisch.
