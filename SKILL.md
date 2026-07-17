---
name: strategy-pipeline
description: "GENERAL-PURPOSE Strategie-Pipeline. Nimmt OBEN irgendeine Problemstellung (Prompt/Textdatei, beliebige Domäne) und läuft VOLLautomatisch durch: (1) 4 analytische Perspektiven (generisch, domän-agnostisch), (2) Consensus-Engine, (3) Strategiebericht, (4) interdisziplinäres Versagens-Register, (5) Peer-Review-Subagent, (6) finaler 1-PDF-Report mit DYNAMISCHER, kontext-aware Länge (kleiner Fall = wenige Seiten, großer = 50+; nie fix). WICHTIG: Die Framework-Namen (Sun Tzu, OODA, Game Theory, Systems, Gabor Maté, Sun Mate) erscheinen NIE im Report — die Perspektiven sind anonyme Werkzeuge ('Perspektive 1–4'). Läuft über den Rust-Orchestrator albert-strategy-orchestrator. Trigger: 'strategie pipeline', 'problemstellung analysiern', 'lauf die pipeline', 'generischer strategie-report', 'mach mir den bericht zu X'."
version: 1.0.0
author: Hermes Agent / RFI-IRFOS
license: MIT
metadata:
  hermes:
    tags: [strategy, pipeline, general-purpose, orchestrator, consensus, peer-review, dynamic-report, domän-agnostisch]
    related_skills: [sun-mate, ooda, systems, game-theory, strategy-orchestrator, failure-audit, context-audit, fact-audit, final-factcheck]
---

# Strategy Pipeline (General-Purpose)

## Branding & Namensgebung (WICHTIG — HARTE REGEL VOM USER, WÖRTLICH)

User-Quote: *"wir sind eine firma keine kochshow wir nennen es IMMER
brillen [Perspektiven], aber nicht linsen bitte"* + *"die laura
killt uns sie sagt wir sind eine firma keine kochshow"*.

- **KEINE Personen-Marke.** Die Pipeline isch a FIRMA-Werkzeug
  (RFI-IRFOS), kane Kochshow. Sie wird NIE nach am Testfall benannt.
  Wer sie nach einem einzelnen Testfall benennt, hat des Design ned
  kapiert.
- **Perspektiven = "Perspektive 1–4" / neutral "Viewpoints".**
  **NIE "Linsen" / "Lenses" / "Laura's X" / a personen-gebundener
  Name.** "Linsen" (Lenses) klingt nach Kochshow/Personen-Marke —
  des killt uns. Ein analytisches Werkzeug isch kane Marke.
  (Im Code/HTML ausschließlich `Perspektive`/`Viewpoint` verwenden;
  `grep -i 'linse'` auf den Report darf NICHTS liefern.)
- **KEIN "Laura-Pipeline" / kein Testfall-Name im Report.** Der
  Testfall isch austauschbar, ned das Produkt. Im general-purpose
  Report wird der Testfall-Name durch generische Begriffe ersetzt
  (z.B. "Laura" → "Auftraggeberin"). Verify: `grep -i 'laura'` = leer.
- **Framework-Namen im Report:** Gabor Maté, Sun Tzu, Sun Mate, OODA,
  Game Theory, Systems Thinking erscheinen **NIE** im Report.
- **Neutraler Output:** Der Report steht als sachlicher Lagebericht.
  "es isch einfach so" — kane Larifari, kane Selbstdarstellung.

## Härte-Gate (Fact-Audit) — PFLICHT VOR DEM RENDER

Der Report wird NIE aus freier Hand generiert. Jeder Personen-Bezug muss gegen
eine Entity-Ground-Truth (facts.json) verifiziert sein. Sonst: Lauf bricht ab.

User-Quote: *"jja sowas darf nch passiern das müssen wir besser schreiben
dann und die pipeline wirklich astrein machen debug das mal und härte die pipeline"*
(Bezug: Sonia-Fehler — fälschlich als Anzeigenerstatterin deklariert, obwohl
Quelle "nicht anzeigebereit" sagt.)

**Ablauf:**
1. `facts.json` aus den Quellen extrahieren (wer hat Anzeige erstattet, wer
   nur Mitbewohner/Mitwisser — mit Quellenangabe).
2. Nach HTML-Generierung: `fact-audit.py report.html facts.json`
   - Exit 0 = OK → weiter zu Render
   - Exit 1 = HARD FAIL (Sonia-Typ-Fehler / Framework-Name / Linsen) →
     **KEIN PDF**, Lauf bricht ab.
3. Erst nach bestandenem Gate: `strategy-report-render.py` → PDF.

**fact-audit.py prüft:**
- Person mit `anzeigebereit: false` darf NIE mit Anzeige-Verb auftreten (Sonia-Regel)
- Jede Personen-Erwähnung MUSS Quellen-Ref (IMG_/Aktenzeichen) im Text haben
- Framework-Namen (Gabor/Sun Tzu/Sun Mate/OODA/Game Theory/Systems) = HARD FAIL
- "Linsen" / "Laura-Pipeline" / Testfall-Name = HARD FAIL

**Warum das Gate existiert:** Im Testfall wurde Sonia fälschlich als
"Anzeige gegen Osman" deklariert. Die Quelle (02_TIEFENANALYSE §6 Z.92) sagt
explizit "nicht anzeigebereit". Ein Gate hätte das verhindert. Seitdem ist es
nicht optional.

Siehe Skill `fact-audit` für Details + Skript.

## Workflow (mit ALLEN Gates — Reihenfolge PFLICHT)

```
1. Problemstellung → Orchestrator (4 Agenten + Consensus) → consolidated.json
2. HTML-Report generieren (Template + JSON)
3. GATE 1: fact-audit.py <report.html> <facts.json>        → Exit 1 = STOP
4. GATE 2: final-factcheck.py <report.html> <facts.json> --mode llm --sources ./docs
                                                          → Exit 1 = STOP
5. pipeline-render.py <report.html> <facts.json> <out.pdf> → nur wenn Gates PASS
```

Oder via Wrapper: `run-pipeline.sh <mission.txt> <output.pdf> [--sources DIR] [--no-llm]`

**Kein Endreport verlässt die Pipeline ohne beide Gates.** Das ist die Härte:
ein Fakt-Fehler (Sonia-Typ) wird beim zweiten Gate garantiert gefangen,
weil final-factcheck kontextuell liest (nicht nur Pattern wie Gate 1).

Siehe Skills `fact-audit` + `final-factcheck` für Details.

## Was es tut

Nimmt **irgendeine Problemstellung** (ein Prompt, eine Textdatei, ein Fall,
beliebige Domäne — Recht, Business, Konflikt, Organisationsentwicklung,
politische Strategie, Persönlichkes) und produziert **einen einzigen,
konsolidierten Strategie- & Versagensbericht** als PDF.

Die Pipeline ist **domän-agnostisch**. Sie isch NICHT auf den Laura-Testfall
spezialisiert — der diente nur zum Validiern. Jeder neue Prompt läuft
identisch durch.

## Report-Format (USER-ANFORDERUNG — ALLES PFLICHT VOR SHIP)

Der Endreport MUSS so aussehen (jeder Punkt wird vor Auslieferung geprüft):

- **TOC oben:** `<nav class="toc">` mit "Inhaltsverzeichnis", römisch
  nummeriert (I, II, III, IV + II.1–II.12), **anklickbare Anker-Links**
  (`href="#..."`, ~16 Stück). Chrome ignoriert CSS `page-break` auf
  top-level `<h2>` zuverlässig — deshalb Sektionen via `<div class="divider">`
  splitten und einzeln rendern + `pdfunite` mergen (siehe scripts/).
- **Römisch durchgehend:** Hauptebenen I/II/III/IV. Verify:
  `pdftotext | grep -cE '^(I|II|III|IV)\.'` > 0.
- **Kanonisches RFI-IRFOS Richtext-CSS:** Helvetica Neue, #111/#333/#666,
  `.stamp` (Courier uppercase), `.subtitle`, `.quote`, `.note-box`,
  `.caveat-box`, `table.pattern`. Stil: ruhig, fachlich, kane Deko.
  (Quelle: irgendein RFI-IRFOS `bericht.html` — exakt übernehmen.)
- **Whitebox-Breakdown (Ebene 0):** VOLLSTÄNDIG im Report (ganz oben nach
  TOC). Alle aktiven Agenten auflisten: wer, was war ihr Output, wie haben
  sie entschieden. Plus Konsens-Engine-Ergebnis (Score, alle einig?).
  Plus Agenten-Entscheidungsmatrix + Prinzipien-Tabelle pro Agent.
  User (wörtlich): *"die komplette breakdown von allen agenten die aktiv
  waren und was deren output war und wie die entschieden haben, volle
  whitebox"*.
- **Dynamische Länge:** Substanz bestimmt Seitenzahl, NIE fix. User wollte
  min. 15, dann 20+. Kleiner Fall = 3–5, großer = 50+. Hebel für mehr
  Seiten: CSS `line-height`/`margin` auflockern + echte Sektionen
  (Anhänge A/B/C), NIE erfundenen Content paden.
- **STRATEGIE-SCHRITTE BLOCK (PFLICHT — User-Catch):** Ganz unten in
  Ebene 2 MUSS a Sektion **"Strategische Schritte (Implementierung)"**
  stehen — Phasen (Sofort Woche 1–2 / Kurzfristig Monat 1–3 /
  Mittelfristig Monat 3–12), konkrete nummerierte Schritte (mit
  COA-Zuordnung + Quelle/Begründung), plus Entscheidungspunkte +
  Warnzeichen. User (wörtlich): *"wo isch der block ganz unten wo die
  strategischen schritte geschrieben werden? :D das ehlt oder"*. Ohne
  diesen Block = Report unvollständig, User merkt's SOFORT.
- **4 Ebenen:** (0) Whitebox · (I) Perspektiven · (II) Lagebericht ·
  (III) Versagens-Register.

## Die 4 analytischen Perspektiven (anonym, generisch)

Die Pipeline nutzt 4 unabhängige analytische Perspektiven. Im Report
erscheinen sie NIE namentlich — nur als **Perspektive 1–4** mit
thematischer Beschreibung. Sie sind Werkzeuge, keine Akteure.

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

## Dynamische, kontext-aware Länge (User-Voice: "muss immer dynamisch sein")

Der Report isch **nie fix lang**. Länge richtet sich nach der
Komplexität der Problemstellung — vom User explizit gefordert
(*"8 seiten isch mir zu wenig... das muss immer dynamisch sein,
wenn ein 50 seiten report rauskommen soll dann ok, wenn nich dann
nich, es muss kontext aware sein"*).

- **Kleiner Fall** (einfache Entscheidung): ~3–5 Seiten.
- **Mittlerer Fall**: ~10–15 Seiten.
- **Großer Fall** (viele Akteure, viele Dokumente, viele Versagen):
  20–50+ Seiten.

**HÄRTE REGEL:** Bei einem KOMPLEXEN Fall den Report KEIN 8-Seiten-
Report kappen. User-Clear: *"Mindestens bei dem fall ein 15 seiten
report dasteht mit allen details der nix zurückhält also MINDESTENS."*
Wenn Substanz da isch → mehr Seiten. Wenn a klarer, kleiner Fall
vorligt → kurz sein, ned 50 Seiten erzwingen.

Mechanik (im Renderer `scripts/strategy-report-render.py`): HTML wird
an `.divider`-Sektionen gesplittet, jede Sektion EINZELN mit
Chrome gerendert, dann mit `pdfunite` gemerged. `break-before:
page` auf `.divider` respektiert Chrome-headless zuverlässig pro
separat gerendertem Part (NICT im Gesamt-HTML — bekannter Bug).

## KEINE Framework-Namen im Report (HÄRTESTE REGEL — User, wiederholt)

Striker Grundsatz: Im finalen PDF erscheinen **NIE**: "Gabor Maté",
"Sun Tzu", "Sun Mate", "OODA", "Game Theory", "Systems Thinking",
oder ähnliches. Die Perspektiven sind anonyme Werkzeuge
("Perspektive 1–4"), nie namentlich benennt.

User-Voice (wörtlich): *"es soll nirgendwo im report gabor mate
oder so schreiben oder die stimmen von denen, es ISCH einfch so wir
wissen das."* — Die Analyse-Werkzeuge sind Werkzeuge. Ihre Identität
isch für die Lesbarkeit des Berichts irrelevant. Der Bericht soll als
direkter, neutraler Lagebericht stehen.

**VERIFIKATION (zwingend, VOR Auslieferung):**
```bash
pdftotext <report>.pdf - 2>/dev/null | grep -i "gabor\|sun tzu\|sun mate\|ooda\|game theory\|systems thinking"
# LEER = OK. JEDER Treffer = Fehler, vor Auslieferung fixen.
# ZUSATZ (Branding): auf dem HTML, nicht nur PDF:
grep -i "linse" <report>.html   # LEER = OK (nie "Linsen")
grep -i "laura" <report>.html   # LEER = OK (Testfall anonymisiert)
grep -c 'href="#' <report>.html # > 10 = TOC-Anker vorhanden
```
Der Peer-Review-Subagent prüft Namens-Leakage als PUNKT 1.
Auch sprachliche Kokettage ("wiederholtes Spiel", "Gleichgewicht"
bei Perspektive 4) isch unkritisch, solange der Framework-NAME ned
fällt — aber lieber meiden.

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

## Output-Struktur (1 PDF, 4 Ebenen — Ebene 0 = Whitebox GANZ OBEN)

```
EBENE 0 — Agent-Breakdown (Whitebox)  ← MUSS ganz oben nach TOC stehen
  - Welche Agenten waren aktiv (Perspektive 1–4)
  - Was war ihr Output (empfohlene COA, Narrative)
  - Wie haben sie entschieden (Prinzipien + Begründung)
  - Konsens-Engine: Score, alle einig?, empfohlene Blend
  - Agenten-Entscheidungsmatrix (Primär/Parallel/Option/Fallback je Agent)
  - Detaillierte Prinzipien-Anwendung pro Agent (Tabelle)
  - Methodik: Isolation vor Aggregation (verhindert Groupthink)
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
  - **Strategische Schritte (Implementierung) — PFLICHT, GANZ UNTEN in Ebene 2**
    (Phasen: Sofort/Kurzfristig/Mittelfristig; konkrete nummerierte Schritte
     mit COA + Quelle; Entscheidungspunkte + Warnzeichen)
EBENE 3 — Interdisziplinäres Versagens-Register
  (jeder Eintrag: was schief lief, Gesetz, warum kritisch,
   Mitigation, Gegenseite, 3 Optionen)
+ Anhänge A/B/C (Pipeline-Architektur, Problemstellung, Fehler-Detail)
```

## Integration mit anderen Skills

- `sun_mate`, `ooda`, `systems`, `game_theory`: Die 4 Werkzeug-Skills.
- `strategy-orchestrator`: Der Rust-Orchestrator-Wrapper.
- `failure-audit`: Das Versagens-Register (Ebene 3).
- `context-audit`: Findet übersehene Nuancen (Input für Ebene 2).
- `references/chrome-split-render-recipe.md`: Das PDF-Split-Render-
  Merge-Rezept + `patch`-Tool-Umlaut-Pitfall + Namens-Verifikation.
- `templates/report_template.html`: KANONISCHES RFI-IRFOS CSS +
  TOC-Gerüst (römisch + Anker) + alle `.divider`/`.reg`/`.agent-breakdown`
  Klassen. EINFACH kopieren und mit Inhalt füllen — NIE neu erfinden.

## Pitfalls

- **Chrome-headless `break-before` Bug:** Im Gesamt-HTML respektiert
  Chrome `break-before: page` nicht zuverlässig (bleibt bei ~8
  Seiten hängen, egal wieviele Umbrüche). LÖSUNG: HTML an
  `.divider` in Sektionen splittn, JEDE einzeln mit Chrome rendern,
  mit `pdfunite` mergen. So kommen 25–50+ Seiten raus.
- **`patch`-Tool zerstört Rust mit Umlauten:** Beim Patchen von
  `.rs`-Dateien mit deutschen Umlauten im Kommentar/Strings
  produziert des `patch`-Tool Formatierungs-Chaos (rustfmt-
  Diffs, verschobene Klammern). Bei Rust-Dateien lieber
  `write_file` (komplett neu schreiben) oder `execute_code`
  zum String-Ersetzen nutzen, NICT `patch`.
- **Framework-Namen:** Strikt vermeiden im Report. Vor Auslieferung
  mit `pdftotext | grep` verifiziern (siehe oben). Peer-Review
  prüft als PUNKT 1. ZUSÄTZLICH verify: `grep -i 'linse'` und
  `grep -i 'laura'` auf dem HTML = leer (Personen-Marke/Linsen = fail).
- **"Linsen"/"Laura" im Report:** Nie verwenden. Immer "Perspektive 1–4"
  bzw. generischen Testfall-Begriff ("Auftraggeberin"). User-Härte:
  "wir sind eine firma keine kochshow, nennen es Perspektiven, nicht
  Linsen". Ein analytisches Werkzeug isch kane Marke.
- **Whitebox (Ebene 0) nicht vergessen:** User will VOR dem Lagebericht
  die volle Breakdown aller Agenten (Output + Entscheidung + Konsens).
  Ohne Ebene 0 isch der Report unvollständig.
- **Fakt-Checking (INDIVIDUEN-EXTRAPOLATION — User-Catch):** Jede Aussage ueber eine konkrete Person MUSS auf eine Quelle zurueckfuehrbar sein (Dateiname / Zeilennummer). NIE aus aehnlichen Faellen extrapoliern. User-Catch: im Report stand "Sonia (20 J., indonesisch): Anzeige gegen Osman" — DES WAR FALSCH. Quelle (02_TIEFENANALYSE Z.92) sagt explizit "nicht anzeigebereit". Sonia ist Mitbewohnerin, KEIN Anzeigende. Lesson: Eine Liste von "Anzeigenerstatterinnen" darf nur Namen enthalten, die in den Quellen explizit als Anzeigende benennt sind. "Mehrheitlich mit Migrationshintergrund" + "Statusangst" = Kontext, nicht gleich "hat Anzeige erstattet". Vor Auslieferung Fakt-Check: jeder Name im Report gegen die Quelldokumente (grep im .md der Fallakte) verifiziern, nicht nur gegen die eigenen Analyse-JSONs.
- **"Strategische Schritte (Implementierung)" Block NICHT vergessen:**
  Ganz unten in Ebene 2 MUSS diese handlungsorientierte Sektion stehen
  (Phasen + nummerierte Schritte + Entscheidungspunkte/Warnzeichen).
  User hat im fertigen 21-Seiten-Report SOFORT gemerkt dass der Block
  fehlt ("wo isch der block ganz unten… des ehlt oder"). Vor Auslieferung
  verifiziern: `pdftotext | grep -c 'Strategische Schritte'` ≥ 1.
- **TOC + römisch + Anker:** Report MUSS TOC oben (römisch I/II/III/IV),
  anklickbare `href="#"`-Links, kanonisches RFI-IRFOS CSS. Verify:
  `pdftotext | grep -cE '^(I|II|III|IV)\.'` > 0 UND
  `grep -c 'href="#' report.html` > 10.
- **Dynamische Länge:** Nicht fix kappen. Substanz bestimmt
  Seitenzahl. Komplexer Fall → MINDESTENS 15 Seiten, nie 8.
- **Domän-agnostisch bleiben:** Die Pipeline isch generisch. Laura
  war NUR der Testfall. Jeder neue Prompt läuft identisch —
  die Skill-Beschreibung und Beispiele müssen das klarmachen.
- **Peer-Review darf ned schreiben:** Nur Feedback, Haupt-Instanz
  baut ein. Subagent darf KEINE Dateien verändern.
- **Orchestrator braucht echte Analyse-JSONs:** `load_reports_for`
  liest `<skill>_analysis.json` aus dem Fallordner. Für 100%
  general-purpose müssten die Analyse-Skills pro Prompt frisch
  analysiern (ned aus ainer fixes JSON lesen) — aktuell no offen.

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
