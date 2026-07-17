#!/usr/bin/env bash
# ============================================================================
# RFI-IRFOS Strategy-Pipeline — E2E
# ============================================================================
set -euo pipefail

# Farben
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# Pfade
BASE="/home/eri-irfos/Desktop/do it for laura "
RUST_BIN="/home/eri-irfos/projects/albert-strategy-orchestrator/target/release/albert-strategy-orchestrator"
SCRIPTS="/home/eri-irfos/.hermes/skills/strategy/strategy-pipeline/scripts"
LOG="$BASE/logs/pipeline_$(date +%Y%m%d_%H%M%S).log"

# Defaults
MISSION="${1:-$BASE/mission_sun_tzu.txt}"
TITLE="${2:-RFI-IRFOS Strategiebericht}"
OUT_PDF="$BASE/strategy_report.pdf"
DESKTOP_PDF="/home/eri-irfos/Desktop/strategy_report.pdf"

# Logging
exec > >(tee -a "$LOG") 2>&1

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

# Check Dependencies
check_deps() {
    info "Check Dependencies..."
    command -v python3 >/dev/null 2>&1 || fail "python3 nicht gefunden"
    command -v xelatex >/dev/null 2>&1 || fail "xelatex nicht gefunden"
    [[ -x "$RUST_BIN" ]] || fail "Rust-Binary nicht gefunden: $RUST_BIN"
    ok "Dependencies OK"
}

# Check Skills
check_skills() {
    info "Check Skills..."
    for skill in sun_mate ooda systems game_theory; do
        [[ -d "$HOME/.hermes/skills/strategy/$skill" ]] || fail "Skill fehlt: $skill"
    done
    ok "Alle Skills vorhanden"
}

# ============================================================================
# Pipeline Steps
# ============================================================================

info "=== STEP 1: Orchestrator ==="
time "$RUST_BIN" --skills all --mission "$MISSION" --out "$BASE/orchestrator_consolidated.json" 2>&1 | tail -10
ok "Orchestrator fertig"

info "=== STEP 2: Strategy-Spec bauen ==="
python3 "$SCRIPTS/build_strategy_spec.py" \
    "$BASE/orchestrator_consolidated.json" \
    "$BASE/facts.json" \
    "$BASE/strategy_report_spec.json" \
    --title "$TITLE" 2>&1 | tail -3
ok "Spec gebaut"

info "=== STEP 3: Fact-Audit (Pattern) ==="
python3 "$HOME/.hermes/skills/strategy/fact-audit/scripts/fact-audit.py" \
    "$BASE/strategy_report_spec.json" \
    "$BASE/facts.json" 2>&1 | tail -3
ok "Fact-Audit bestanden"

info "=== STEP 4: Final Fact-Check (Pattern) ==="
python3 "$HOME/.hermes/skills/strategy/final-factcheck/scripts/final-factcheck.py" \
    "$BASE/strategy_report_spec.json" \
    "$BASE/facts.json" \
    --mode pattern --sources "$BASE" 2>&1 | tail -3
ok "Final Fact-Check bestanden"

info "=== STEP 5: PDF rendern ==="
python3 "$SCRIPTS/gen_report.py" \
    "$BASE/strategy_report_spec.json" \
    "$OUT_PDF" 2>&1 | tail -3
ok "PDF gerendert"

info "=== VERIFY ==="
PAGES=$(pdfinfo "$OUT_PDF" 2>/dev/null | grep Pages | awk '{print $2}' || echo "?")
LEAKS=$(pdftotext "$OUT_PDF" - 2>/dev/null | grep -ic "sun tzu\|gabor\|ooda\|game theory\|systems thinking\|sun_mate\|laura" || echo "0")
BOOKMARKS=$(mutool show "$OUT_PDF" outline 2>/dev/null | wc -l || echo "?")

echo -e "${GREEN}─────────────────────────────────────────${NC}"
echo -e "${GREEN}  Pipeline ERFOLGREICH${NC}"
echo -e "${GREEN}─────────────────────────────────────────${NC}"
echo -e "  Seiten   : $PAGES"
echo -e "  Bookmarks: $BOOKMARKS"
echo -e "  Leaks    : $LEAKS (soll 0 sein)"
echo -e "  PDF      : $OUT_PDF"
echo -e "  Log      : $LOG"
echo -e "${GREEN}─────────────────────────────────────────${NC}"

# Auf Desktop kopieren + öffnen
cp "$OUT_PDF" "$DESKTOP_PDF"
ok "PDF auf Desktop kopiert: $DESKTOP_PDF"

# Öffnen (optional, kann übersprungen werden)
if command -v xdg-open >/dev/null 2>&1; then
    info "Öffne PDF..."
    xdg-open "$DESKTOP_PDF" 2>/dev/null || warn "Konnte PDF nicht öffnen"
fi

ok "PIPELINE KOMPLETT DURCHGELAUFEN"
