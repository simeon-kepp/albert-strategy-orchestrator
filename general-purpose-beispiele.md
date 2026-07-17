# Strategy Pipeline — General-Purpose Beispiele

Die Pipeline isch **domän-agnostisch**. Laura war NUR der Testfall.
Jeder neue Prompt läuft identisch durch.

## Beispiel 1: Business-Konflikt

```
Problemstellung (prompt):
"Analyier mir den Konflikt zwischen Team A (Engineering)
und Team B (Product) wegen Ressourcen-Allokation in
unserer Firma. Team A will mehr Headcount, Team B blockt."

→ Pipeline läuft:
  4 Perspektiven → Consensus → Strategiebericht →
  Versagens-Register → Peer-Review → 1 PDF (dyn. Länge)
→ Output: total_report.pdf (z.B. 12 Seiten für diesen Fall)
```

## Beispiel 2: Rechtlicher Fall (wie Laura, aber generisch)

```
Problemstellung (Textdatei):
"Fall X: Beschuldigter Y, drei unabhängige Zeuginnen,
Einstellung als 'privat'. Aktenzeichen 123 Js 456/24.
Bitte Strategiebericht."

→ Pipeline läuft identisch.
```

## Beispiel 3: Persönliche Entscheidung

```
Problemstellung (prompt):
"Soll ich das Job-Angebot annehmen oder bleiben?
Pro: mehr Geld. Contra: Umzug. Mach mir den Bericht."

→ Pipeline läuft identisch.
```

## WICHTIGE Regeln (im Report)

1. **KEINE Framework-Namen** — Perspektiven sind anonym
   ("Perspektive 1–4"), nie "Sun Tzu" / "OODA" etc.
2. **Dynamische Länge** — Substanz bestimmt Seitenzahl,
   nie fix. Kleiner Fall = wenige Seiten, großer = 50+.
3. **1 PDF am Ende** — konsolidiert, 3 Ebenen.
4. **Peer-Review** — second pass stärkt den Draft.

## CLI

```bash
# 1) Orchestrator (4 Skills konsolidiern)
cd /home/eri-irfos/projects/albert-strategy-orchestrator
cargo build
./target/debug/albert-strategy-orchestrator \
  --skills sun_mate,ooda,systems,game_theory \
  --mission <problemstellung.txt> \
  --out <konsolidated.json>

# 2) Report rendern (dynamische Länge)
python3 ~/.hermes/skills/strategy/strategy-pipeline/scripts/strategy-report-render.py \
  <konsolidated.json> <output.pdf> \
  --html-template <total_report.html>
```
