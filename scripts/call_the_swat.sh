#!/usr/bin/env bash
# ============================================================================
# call_the_swat — Launch-Script für die RFI-IRFOS Strategy-Pipeline
#
# Doppelklick auf Desktop → Terminal öffnet sich → Mission auswählen →
# Vollautomatischer Durchlauf → Report am Ende.
#
# Usage (Terminal):
#   ./call_the_swat.sh [mission.txt]
#
# Ohne Argument: interaktive Auswahl aus /home/eri-irfos/Desktop/do it for laura /
# ============================================================================

set -euo pipefail

# ── Farben ──
RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[1;33m'
BLU='\033[0;34m'
MAG='\033[0;35m'
CYN='\033[0;36m'
WHT='\033[1;37m'
RST='\033[0m'

# ── Pfade ──
BASE_DIR="/home/eri-irfos/Desktop/do it for laura "
MISSION_DIR="$BASE_DIR"
SKILL_DIR="/home/eri-irfos/.hermes/skills/strategy"
ORCH_SCRIPT="$SKILL_DIR/strategy-orchestrator/scripts/strategy-orchestrator.sh"
BUILD_SPEC="$SKILL_DIR/strategy-pipeline/scripts/build_strategy_spec.py"
FACT_AUDIT="$SKILL_DIR/fact-audit/scripts/fact-audit.py"
FINAL_CHECK="$SKILL_DIR/strategy-pipeline/scripts/final-factcheck.py"
GEN_REPORT="$SKILL_DIR/strategy-pipeline/scripts/gen_report.py"
FACTS="$SKILL_DIR/strategy-pipeline/scripts/facts.json"
OUTPUT_DIR="/home/eri-irfos/Desktop"
RUST_BIN="/home/eri-irfos/projects/albert-strategy-orchestrator/target/debug/albert-strategy-orchestrator"

# ── Helpers ──
hr()   { printf "${BLU}%s${RST}\n" "────────────────────────────────────────────────────────────"; }
info() { printf "${GRN}[INFO]${RST} %s\n" "$1"; }
warn() { printf "${YEL}[WARN]${RST} %s\n" "$1"; }
fail() { printf "${RED}[FAIL]${RST} %s\n" "$1"; }
header(){ printf "\n${MAG}╔══════════════════════════════════════════════════════════════╗${RST}\n"; printf "${MAG}║${RST}  %-60s${MAG}║${RST}\n" "$1"; printf "${MAG}╚══════════════════════════════════════════════════════════════╝${RST}\n"; }

# ── Dependency-Check ──
check_deps() {
  header "SWAT DEPLOYMENT — Dependency Check"
  local missing=0

  # Python
  if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
    info "python3 $PY_VER"
  else
    fail "python3 nicht gefunden!"
    missing=1
  fi

  # xelatex
  if command -v xelatex &>/dev/null; then
    info "xelatex $(xelatex --version 2>&1 | head -1 | grep -oP '[\d.]+')"
  else
    fail "xelatex NICHT gefunden! → sudo apt install texlive-xetex"
    missing=1
  fi

  # Fonts
  if fc-list 2>/dev/null | grep -qi "inter"; then
    info "Inter Font"
  else
    warn "Inter Font nicht gefunden — Fallback wird verwendet"
  fi

  # Rust Binary
  if [[ -x "$RUST_BIN" ]]; then
    info "Rust Orchestrator (albert-strategy-orchestrator)"
  else
    warn "Rust-Binary nicht gefunden — baue ihn jetzt..."
    if [[ -d "$BASE_DIR" ]]; then
      (cd "$BASE_DIR" && cargo build --release 2>/dev/null || cargo build 2>/dev/null) || {
        fail "cargo build fehlgeschlagen!"; exit 1;
      }
      RUST_BIN="$BASE_DIR/target/release/albert-strategy-orchestrator"
      [[ -x "$RUST_BIN" ]] && info "Rust-Binary gebaut" || { fail "Binary trotz Build nicht gefunden"; exit 1; }
    else
      fail "$BASE_DIR nicht gefunden!"; exit 1;
    fi
  fi

  # Hermes Skills
  for skill in sun_mate ooda systems game_theory; do
    if [[ -d "$SKILL_DIR/$skill" ]]; then
      info "Skill: $skill"
    else
      warn "Skill $skill nicht gefunden!"
      missing=1
    fi
  done

  # Scripts
  for script in "$BUILD_SPEC" "$FACT_AUDIT" "$FINAL_CHECK" "$GEN_REPORT"; do
    if [[ -f "$script" ]]; then
      info "$(basename "$script")"
    else
      fail "$(basename "$script") NICHT gefunden!"
      missing=1
    fi
  done

  # facts.json
  if [[ -f "$FACTS" ]]; then
    info "facts.json (Ground-Truth)"
  else
    warn "facts.json nicht gefunden!"
  fi

  hr

  if [[ $missing -eq 1 ]]; then
    fail "Fehlende Dependencies — Pipeline kann nicht gestartet werden."
    read -rp $'\nPress ENTER zum Beenden...'
    exit 1
  fi

  info "Alle Dependencies OK — SWAT-Team ist einsatzbereit."
}

# ── Mission auswählen ──
select_mission() {
  header "MISSION BRIEFING — Auswählen"

  # Falls Argument mitgegeben wurde
  if [[ -n "${1:-}" ]]; then
    MISSION_FILE="$1"
    if [[ -f "$MISSION_FILE" ]]; then
      info "Mission: $(basename "$MISSION_FILE")"
      return 0
    else
      fail "$MISSION_FILE nicht gefunden!"
      exit 1
    fi
  fi

  # Suche mission*.txt im Mission-Dir
  shopt -s nullglob
  local missions=()
  for f in "$MISSION_DIR"/mission*.txt; do
    [[ -f "$f" ]] && missions+=("$f")
  done
  shopt -u nullglob

  if [[ ${#missions[@]} -eq 0 ]]; then
    warn "Keine mission*.txt in $MISSION_DIR gefunden."
    read -rp "Pfad zur Mission eingeben (oder ENTER zum Abbruch): " custom_path
    if [[ -z "$custom_path" ]]; then
      fail "Keine Mission — Abbruch."
      exit 1
    fi
    MISSION_FILE="$custom_path"
    return 0
  fi

  echo ""
  printf "${WHT}Verfügbare Missionen:${RST}\n"
  for i in "${!missions[@]}"; do
    local name=$(basename "${missions[$i]}")
    local size=$(wc -c < "${missions[$i]}")
    printf "  ${CYN}[%d]${RST} %-40s (%d bytes)\n" "$((i+1))" "$name" "$size"
  done
  echo ""
  read -rp "Mission auswählen [1-${#missions[@]}] oder ENTER für neueste: " choice

  if [[ -z "$choice" ]]; then
    # Neueste nehmen
    MISSION_FILE=$(ls -t "${missions[@]}" | head -1)
  elif [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#missions[@]} )); then
    MISSION_FILE="${missions[$((choice-1))]}"
  else
    fail "Ungültige Auswahl!"
    exit 1
  fi

  info "Mission: $(basename "$MISSION_FILE")"
}

# ── Bestätigung ──
confirm_run() {
  header "BESTÄTIGUNG"
  printf "${WHT}Mission:${RST}      %s\n" "$(basename "$MISSION_FILE")"
  printf "${WHT}Output:${RST}       %s\n" "$OUTPUT_DIR/strategiebericht_$(date +%Y%m%d_%H%M%S).pdf"
  printf "${WHT}Gates:${RST}        Fact-Audit (Pattern) → Final-Factcheck (LLM) → xelatex\n"
  printf "${WHT}Agents:${RST}       4 Perspektiven (Sun Mate / OODA / Systeme / Spieltheorie)\n"
  hr
  read -rp $'\n[ENTER] Pipeline starten — [Ctrl+C] Abbruch\n'
}

# ── Pipeline ──
run_pipeline() {
  local timestamp=$(date +%Y%m%d_%H%M%S)
  local OUTPUT_PDF="$OUTPUT_DIR/strategiebericht_${timestamp}.pdf"
  local WORKDIR="$BASE_DIR"
  local CONSOLIDATED="$WORKDIR/orchestrator_consolidated.json"
  local SPEC="$WORKDIR/strategy_report_spec.json"
  local LOGFILE="$WORKDIR/pipeline_${timestamp}.log"

  header "PIPELINE GESTARTET — $(date '+%Y-%m-%d %H:%M:%S')"
  printf "${WHT}Log:${RST} %s\n\n" "$LOGFILE"

  # ── Step 1: Orchestrator ──
  header "Step 1/5 — Orchestrator (4 Agenten + Consensus)"
  info "Starte Rust-Orchestrator..."
  if [[ -x "$RUST_BIN" ]]; then
    "$RUST_BIN" --skills sun_mate,ooda,systems,game_theory --mission "$MISSION_FILE" --out "$CONSOLIDATED" 2>&1 | tee "$LOGFILE"
  else
    fail "Orchestrator-Binary nicht gefunden!"
    exit 1
  fi

  if [[ ! -f "$CONSOLIDATED" ]]; then
    fail "orchestrator_consolidated.json wurde nicht erstellt!"
    exit 1
  fi
  info "Consolidated JSON erstellt ($(wc -c < "$CONSOLIDATED") bytes)"

  # ── Step 2: Spec bauen ──
  header "Step 2/5 — Strategy-Spec bauen (LaTeX)"
  info "Baue LaTeX-Spec..."
  python3 "$BUILD_SPEC" "$CONSOLIDATED" "$FACTS" "$SPEC" --title "Auftraggeberin-Fall: Strategie & Versagensbericht" 2>&1 | tee -a "$LOGFILE"
  info "Spec erstellt: $(wc -c < "$SPEC") bytes"

  # ── Step 3: Fact-Audit (Pattern) ──
  header "Step 3/5 — Gate 1: Fact-Audit (Pattern)"
  info "Prüfe Facts gegen Spec..."
  if python3 "$FACT_AUDIT" "$SPEC" "$FACTS" 2>&1 | tee -a "$LOGFILE"; then
    info "Gate 1 PASS"
  else
    fail "GATE 1 FEHLGESCHLAGEN — STOP"
    exit 1
  fi

  # ── Step 4: Final-Factcheck (LLM) ──
  header "Step 4/5 — Gate 2: Final-Factcheck (kontextuell)"
  info "LLM-basierter Faktencheck..."
  if python3 "$FINAL_CHECK" "$SPEC" "$FACTS" --mode llm --sources "$WORKDIR" 2>&1 | tee -a "$LOGFILE"; then
    info "Gate 2 PASS"
  else
    warn "Gate 2 WARNUNG (LLM-Check hatte Probleme, aber Pattern-Gate ist PASS)"
    # Nicht hart abbrechen — Pattern-Gate ist die harte Grenze
  fi

  # ── Step 5: Render ──
  header "Step 5/5 — Render (kanonisches obsidian Template)"
  info "Rendere PDF via xelatex..."
  if python3 "$GEN_REPORT" "$SPEC" "$OUTPUT_PDF" 2>&1 | tee -a "$LOGFILE"; then
    :
  else
    fail "Render fehlgeschlagen!"
    exit 1
  fi

  # ── Verify ──
  header "VERIFIZIERUNG"
  local pages
  pages=$(pdfinfo "$OUTPUT_PDF" 2>/dev/null | grep Pages | grep -oP '\d+' || echo "?")

  # Framework-Namen prüfen
  local fw_count
  fw_count=$(pdftotext "$OUTPUT_PDF" - 2>/dev/null | grep -ic "sun tzu\|gabor\|ooda\|game theory\|systems thinking\|sun_mate\|sun tzus\|game_theory\|laura" || echo "0")

  # TOC Bookmarks
  local bookmarks
  bookmarks=$(mutool show "$OUTPUT_PDF" outline 2>/dev/null | wc -l || echo "0")

  info "Seiten:     $pages"
  info "Bookmarks:  $bookmarks (clickbares TOC)"
  info "Leaks:      $fw_count (Framework+Laura — soll 0 sein)"

  if [[ "$fw_count" -gt 0 ]]; then
    warn "Es wurden $fw_count Framework-/Laura-Namen gefunden — prüfe den Report!"
  fi

  # ── Öffnen ──
  header "PIPELINE ABGESCHLOSSEN"
  printf "${GRN}✅ Report:${RST} %s\n" "$OUTPUT_PDF"
  printf "${GRN}✅ Log:${RST}    %s\n" "$LOGFILE"
  hr
  read -rp $'\n[ENTER] Report öffnen — [Ctrl+C] schließen\n'
  xdg-open "$OUTPUT_PDF" 2>/dev/null || open "$OUTPUT_PDF" 2>/dev/null || true
}

# ── Main ──
clear
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██████╗ ██╗      █████╗ ██╗   ██╗███████╗███████╗████████╗      ║
║   ██╔══██╗██║     ██╔══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝      ║
║   ██║  ██║██║     ███████║██║   ██║█████╗  ███████╗   ██║         ║
║   ██║  ██║██║     ██╔══██║██║   ██║██╔══╝  ╚════██║   ██║         ║
║   ██████╔╝███████╗██║  ██║╚██████╔╝███████╗███████║   ██║         ║
║   ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝   ╚═╝         ║
║                                                                      ║
║   ██████╗ ██╗   ██╗██████╗  ██████╗ ██╗   ██╗                      ║
║   ██╔══██╗██║   ██║██╔══██╗██╔═══██╗██║   ██║                      ║
║   ██║  ██║██║   ██║██████╔╝██║   ██║██║   ██║                      ║
║   ██║  ██║██║   ██║██╔══██╗██║   ██║██║   ██║                      ║
║   ██████╔╝╚██████╔╝██║  ██║╚██████╔╝╚██████╔╝                      ║
║   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝                       ║
║                                                                      ║
║            Strategy-Pipeline — RFI-IRFOS (c) 2026                  ║
╚══════════════════════════════════════════════════════════════════════╝
EOF

check_deps
select_mission "${1:-}"
confirm_run
run_pipeline
