# RFI-IRFOS Strategy-Pipeline — Launcher & Scripts

## Desktop-Launcher
**call_the_swat.sh** — zentraler Einstieg, Doppelklick auf Desktop.
**call_the_swat.desktop** — GNOME Desktop-Entry für den Launcher.

## Zentrale Pipeline
**pipeline.sh** — E2E-Pipeline, 5 Steps:
1. Orchestrator: Rust-Binary lädt alle Skills, baut Consensus
2. Strategy-Spec bauen: build_strategy_spec.py wandelt JSON in LaTeX-Spec
3. Fact-Audit (Pattern): Pattern-Check gegen facts.json
4. Final Fact-Check (Pattern): LLM-freier Pattern-Mode
5. PDF rendern: xelatex via gen_report.py (obsidian/black-mirror Theme)

Output: strategy_report.pdf + logs/pipeline_*.log + Desktop-Kopie
