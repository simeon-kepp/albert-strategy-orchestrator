#!/usr/bin/env bash
#
# run-pipeline.sh — Kompletter Strategy-Pipeline-Flow mit ALLEN Gates.
#
# Flow:
#   1. Orchestrator (4 Agenten + Consensus) → consolidated.json
#   2. build_strategy_spec.py → strategy_report_spec.json (LaTeX-Spec)
#   3. Gate 1: fact-audit.py       (Pattern)
#   4. Gate 2: final-factcheck.py  (kontextuell, LLM)
#   5. gen_report.py               (PDF via xelatex, kanonisches obsidian Template)
#
# Bei FAIL in irgendeinem Gate: STOP, kein PDF.
#
# Usage:
#   ./run-pipeline.sh <mission.txt> <output.pdf> [--sources DIR] [--no-llm] [--title T]

set -euo pipefail

MISSION="${1:?Usage: run-pipeline.sh <mission.txt> <output.pdf> [--sources DIR] [--no-llm] [--title T]}"
OUTPUT="${2:?Usage: run-pipeline.sh <mission.txt> <output.pdf> [--sources DIR] [--no-llm] [--title T]}"
shift 2

SOURCES="."
NO_LLM=""
TITLE="Konsolidierter Strategiebericht"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --sources) SOURCES="$2"; shift 2 ;;
    --no-llm)  NO_LLM="--no-llm"; shift ;;
    --title)   TITLE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

SKILL_DIR="/home/eri-irfos/.hermes/skills/strategy"
ORCH="$SKILL_DIR/strategy-orchestrator/scripts/strategy-orchestrator.sh"
BUILD_SPEC="$SKILL_DIR/strategy-pipeline/scripts/build_strategy_spec.py"
FACT_AUDIT="$SKILL_DIR/fact-audit/scripts/fact-audit.py"
FINAL_CHECK="$SKILL_DIR/strategy-pipeline/scripts/final-factcheck.py"
GEN_REPORT="$SKILL_DIR/strategy-pipeline/scripts/gen_report.py"
FACTS="$SKILL_DIR/strategy-pipeline/scripts/facts.json"

WORKDIR="$(dirname "$OUTPUT")"
CONSOLIDATED="$WORKDIR/orchestrator_consolidated.json"
SPEC="$WORKDIR/strategy_report_spec.json"
HTML="$WORKDIR/report_draft.html"

echo "=== [1/5] Orchestrator ==="
"$ORCH" --mission "$MISSION" --out "$CONSOLIDATED" || {
  echo "✗ Orchestrator fehlgeschlagen"; exit 1;
}

echo "=== [2/5] Strategy-Spec bauen (LaTeX) ==="
python3 "$BUILD_SPEC" "$CONSOLIDATED" "$FACTS" "$SPEC" --title "$TITLE" || {
  echo "✗ Spec-Build fehlgeschlagen"; exit 1;
}

echo "=== [3/5] Gate 1: Fact-Audit (Pattern) ==="
python3 "$FACT_AUDIT" "$SPEC" "$FACTS" || {
  echo "✗ GATE 1 FEHLGESCHLAGEN — STOP"; exit 1;
}

echo "=== [4/5] Gate 2: Final Fact-Check (kontextuell) ==="
python3 "$FINAL_CHECK" "$SPEC" "$FACTS" --mode llm --sources "$SOURCES" $NO_LLM || {
  echo "✗ GATE 2 FEHLGESCHLAGEN — STOP"; exit 1;
}

echo "=== [5/5] Render (kanonisches obsidian Template) ==="
python3 "$GEN_REPORT" "$SPEC" "$OUTPUT" || {
  echo "✗ Render fehlgeschlagen"; exit 1;
}

echo ""
echo "✅ PIPELINE KOMPLETT. Endreport: $OUTPUT"
file "$OUTPUT"
