---
name: fact-audit
description: "Härtung der Strategy-Pipeline gegen Fakt-Fehler. Prüft jeden Report-Text gegen eine Entity-Ground-Truth (facts.json) BEVOR gerendert wird. Verhindert dass Personen fälschlich als Anzeigenerstatter/Akteur deklariert werden (wie der Sonia-Fehler). Läuft als Gate vor dem PDF-Render-Schritt."
---

# Fact Audit (Härte-Gate)

## Zweck

Die Pipeline darf keine Fakten frei behaupten. Jeder Personen-Bezug im Report muss gegen
eine **Ground-Truth** (facts.json) verifiziert sein. Dieses Gate läuft VOR dem Rendern —
ein Verstoß bricht den Lauf ab, statt einen falschen Report zu produzieren.

## Wann es läuft

Im `strategy-pipeline` Skill: nach der Report-Generierung (HTML), vor dem PDF-Render.
Das Skript `scripts/fact-audit.py` wird aufgerufen:

```
python3 scripts/fact-audit.py <report.html> <facts.json>
```

Exit-Code 0 = OK. Exit-Code 1 = Fakt-Verstoß (Lauf bricht ab, kein PDF).

## Was es prüft

1. **Anzeige-Bereitschaft:** Jede Person die im Report als "Anzeige gegen X" / "Anzeigenerstatter"
   beschrieben wird, MUSS in facts.json `anzeigebereit: true` haben. Sonst: HARD FAIL.
2. **Quellen-Pflicht:** Jede namentliche Erwähnung einer Person MUSS deren `quelle` im
   Report referenzieren (IMG_/Aktenzeichen). Sonst: WARN.
3. **Negativ-Liste:** Personen mit `anzeigebereit: false` dürfen NIE mit Anzeige-Verben
   (erstattet, zeigte an, klagte) auftreten. Sonst: HARD FAIL.
4. **Framework-Namen:** Gabor Maté, Sun Tzu, Sun Mate, OODA, Game Theory, Systems Thinking
   dürfen NICHT im Report stehen. Sonst: HARD FAIL.
5. **Linsen/Laura:** "Linsen" / "Laura-Pipeline" / namentliche Testfall-Benennung (anonymisiert
   als "Auftraggeberin") dürfen NICHT stehen. Sonst: HARD FAIL.

## facts.json Format

```json
{
  "entities": {
    "Name": {
      "rolle": "Mitbewohnerin",
      "anzeigebereit": false,
      "anzahl_anzeigen": 0,
      "quelle": "02_TIEFENANALYSE §6 Z.92 (IMG_9572-9578)",
      "notiz": "Nicht anzeigebereit"
    }
  },
  "hard_rules": ["..."]
}
```

## Integration in strategy-pipeline

`strategy-pipeline/SKILL.md` ruft nach dem HTML-Write:

```
fact-audit.py report.html facts.json || exit 1
strategy-report-render.py consolidated.json report.pdf --html-template report.html
```

Dadurch: kein falscher Report verlässt die Pipeline.

## Bekannter Vorfall (Sonia-Fehler)

Im Testfall wurde Sonia fälschlich als "Anzeige gegen Osman" deklariert. Quelle
(02_TIEFENANALYSE §6 Z.92) sagt: "nicht anzeigebereit". Dieser Fehler hätte durch
fact-audit.py verhindert werden müssen. Seitdem ist das Gate PFLICHT.
