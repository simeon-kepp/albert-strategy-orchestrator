#!/usr/bin/env bash
#
# run-pipeline.sh — Kompletter Strategy-Pipeline-Flow mit ALLEN Gates.
#
# Flow:
#   1. Orchestrator (4 Agenten + Consensus) → consolidated.json
#   2. HTML-Report generieren (aus Template + JSON)
#   3. Gate 1: fact-audit.py       (Pattern)
#   4. Gate 2: final-factcheck.py  (kontextuell, LLM)
#   5. pipeline-render.py          (PDF, nur wenn Gates PASS)
#
# Bei FAIL in irgendeinem Gate: STOP, kein PDF.
#
# Usage:
#   ./run-pipeline.sh <mission.txt> <output.pdf> [--sources DIR] [--no-llm]

set -euo pipefail

MISSION="${1:?Usage: run-pipeline.sh <mission.txt> <output.pdf> [--sources DIR] [--no-llm]}"
OUTPUT="${2:?Usage: run-pipeline.sh <mission.txt> <output.pdf> [--sources DIR] [--no-llm]}"
shift 2

SOURCES="."
NO_LLM=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --sources) SOURCES="$2"; shift 2 ;;
    --no-llm)  NO_LLM="--no-llm"; shift ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

SKILL_DIR="/home/eri-irfos/.hermes/skills/strategy"
ORCH="$SKILL_DIR/strategy-orchestrator/scripts/strategy-orchestrator.sh"
FACT_AUDIT="$SKILL_DIR/fact-audit/scripts/fact-audit.py"
FINAL_CHECK="$SKILL_DIR/strategy-pipeline/scripts/final-factcheck.py"
RENDER="$SKILL_DIR/strategy-pipeline/scripts/pipeline-render.py"

WORKDIR="$(dirname "$OUTPUT")"
CONSOLIDATED="$WORKDIR/orchestrator_consolidated.json"
HTML="$WORKDIR/report_draft.html"
FACTS="$WORKDIR/facts.json"

echo "=== [1/5] Orchestrator ==="
"$ORCH" --mission "$MISSION" --out "$CONSOLIDATED" || {
  echo "✗ Orchestrator fehlgeschlagen"; exit 1;
}

echo "=== [2/5] HTML-Report generieren ==="
# (Hier würde das Template-Rendering laufen; für Test: Kopie des Templates)
# TODO: Template-Engine die consolidated.json → report_draft.html mappt
cp "$WORKDIR/total_report_v3.html" "$HTML" 2>/dev/null || {
  echo "✗ Kein HTML-Template gefunden"; exit 1;
}

echo "=== [3/5] Gate 1: Fact-Audit (Pattern) ==="
python3 "$FACT_AUDIT" "$HTML" "$FACTS" || {
  echo "✗ GATE 1 FEHLGESCHLAGEN — STOP"; exit 1;
}

echo "=== [4/5] Gate 2: Final Fact-Check (kontextuell) ==="
python3 "$FINAL_CHECK" "$HTML" "$FACTS" --mode llm --sources "$SOURCES" $NO_LLM || {
  echo "✗ GATE 2 FEHLGESCHLAGEN — STOP"; exit 1;
}

echo "=== [5/5] Render (PDF) ==="
python3 "$RENDER" "$HTML" "$FACTS" "$OUTPUT" || {
  echo "✗ Render fehlgeschlagen"; exit 1;
}

echo ""
echo "✅ PIPELINE KOMPLETT. Endreport: $OUTPUT"
file "$OUTPUT"
