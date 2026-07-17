#!/usr/bin/env bash
# ============================================================================
# call_the_swat — Launch-Script für die RFI-IRFOS Strategy-Pipeline
# Doppelklick auf Desktop → Terminal → Mission auswählen → VOLLAUTOMATIK
# ============================================================================

BASE_DIR="/home/eri-irfos/Desktop/do it for laura "
PIPELINE="$BASE_DIR/pipeline.sh"
LOGFILE="$BASE_DIR/logs/launch_$(date +%Y%m%d_%H%M%S).log"

info()  { echo -e "\033[0;34m[INFO]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*"; exit 1; }

mkdir -p "$BASE_DIR/logs"

# Dependency-Check
info "Checke Dependencies..."
command -v python3 >/dev/null 2>&1 || fail "python3 nicht gefunden"
command -v xelatex >/dev/null 2>&1 || fail "xelatex nicht gefunden"
[[ -x "/home/eri-irfos/projects/albert-strategy-orchestrator/target/release/albert-strategy-orchestrator" ]] || fail "Rust-Binary nicht gebaut"
[[ -f "$PIPELINE" ]] || fail "Pipeline nicht gefunden: $PIPELINE"
ok "Alle Dependencies OK"

# Mission auswählen
echo ""
echo "════════════════════════════════════════════"
echo "  RFI-IRFOS Strategy-Pipeline"
echo "════════════════════════════════════════════"
echo ""
echo "Wähle Mission:"
select MISSION_FILE in "$BASE_DIR"mission_*.txt; do
    [[ -n "$MISSION_FILE" ]] && break
    echo "Ungültige Auswahl."
done
echo ""
info "Mission: $(basename "$MISSION_FILE")"
echo ""

# Pipeline starten
info "Starte Pipeline..."
bash "$PIPELINE" "$MISSION_FILE" 2>&1 | tee "$LOGFILE"

echo ""
echo "════════════════════════════════════════════"
echo "  Fertig. Log: $LOGFILE"
echo "════════════════════════════════════════════"
read -p "[ENTER] zum Beenden..."
