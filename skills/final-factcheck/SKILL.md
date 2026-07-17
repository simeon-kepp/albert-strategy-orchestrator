---
name: final-factcheck
description: "EXTRA Fact-Checker Gate der Strategy-Pipeline. Läuft NACH der Report-Generierung, VOR dem PDF-Render — liest den VOLLEN Endreport kontextuell durch und cross-checkt jede Fakt-Behauptung gegen die Quell-Docs (00/02/03/04), BEVOR er rausgeht. Zweite Instanz (Lauras Prinzip: 'nie wie ich'). Verhindert Fakt-Fehler wie den Sonia-Vorfall. Härter als fact-audit (kontextuell, nicht nur Pattern)."
---

# Final Fact-Check (Extra Gate BEVOR der Endreport rausgeht)

## Zweck

Ein zweites, unabhängiges Gate. Nachdem der Report geschrieben ist, aber
BEVOR er als PDF rausgeht, wird der **vollständige** Endreport von einer
zweiten Instanz kontextuell durchgelesen. Jede Behauptung wird gegen die
Quell-Dokumente geprüft.

User-Quote: *"der workflow krigt ein extraa facchecker gate noch BEVOR der
endreport geschrieben wird der nochmal ALLES durchliest BEVOR es rausgeht"*

(Präzision: technisch läuft es NACH dem HTML-Write, VOR dem PDF-Render —
also "bevor es rausgeht" im Sinne von "bevor der Endreport final ausgeliefert
wird".)

## Warum ein zweites Gate?

- `fact-audit` ist Pattern-basiert (schnell, deterministisch): Person
  anzeigebereit=false + Anzeige-Verb = FAIL.
- `final-factcheck` ist kontextuell: ein Subagent liest den ganzen Report
  und findet Widersprüche die Pattern nicht sehen (z.B. falsche Datum-
  zuordnung, falsch interpretierte Quelle, Zahl die nicht stimmt).

Zwei unabhängige Instanzen = Lauras Prinzip "mach wie laura, nie wie ich".
Die zweite Instanz fängt was die erste übersehen hat.

## Ablauf im Workflow

```
1. Problemstellung → Orchestrator (4 Agenten + Consensus)
2. HTML-Report generieren
3. fact-audit.py        ← Gate 1 (Pattern)
4. final-factcheck.py   ← Gate 2 (kontextuell, LLM-Subagent)
5. pipeline-render.py   ← PDF (nur wenn beide Gates PASS)
```

Bei FAIL in Gate 2: **KEIN PDF**, Lauf bricht ab. Report geht nicht raus.

## Skript

`strategy-pipeline/scripts/final-factcheck.py`:

```
# Pattern-Modus (schnell, deterministisch):
python3 final-factcheck.py report.html facts.json --mode pattern

# LLM-Modus (kontextuell, delegiert an Subagent):
python3 final-factcheck.py report.html facts.json --mode llm --sources /pfad/zu/docs
```

- `--mode pattern`: prüft Personen/Anzeige/Framework/Brand (wie fact-audit,
  aber zusätzlich als zweite Meinung).
- `--mode llm`: zusätzlich Subagent der den vollen Report gegen 02/03/04
  cross-checkt. Retourniert `KONFLIKT:`-Zeilen bei Fund.

## Was es fängt (Beispiele)

- Person fälschlich als Anzeigenerstatterin (Sonia-Vorfall)
- Aktenzeichen/Datum falsch zugeordnet
- Quellen-Ref fehlt oder widerspricht der Quelle
- Framework-Name im Report
- "Linsen" / "Laura-Pipeline" / Testfall-Name

## Integration

Im `strategy-pipeline` SKILL.md zwischen "HTML-Write" und "Render":

```
fact-audit.py report.html facts.json || exit 1
final-factcheck.py report.html facts.json --mode llm --sources ./docs || exit 1
pipeline-render.py report.html facts.json final.pdf
```

Ohne beide Gates: kein Endreport.
