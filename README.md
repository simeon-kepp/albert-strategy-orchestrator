# albert-strategy-orchestrator

Multi-Framework Strategy Orchestrator (Rust CLI).

Lädt mehrere Strategy-Skills aus `~/.hermes/skills/strategy/`, validiert sie
gegen `schema.json`, führt eine Consensus-Engine aus und schreibt einen
konsolidierten JSON-Report + CLI-Zusammenfassung.

## Strategy Skill-Familie

| Skill | Framework | Rolle |
|-------|-----------|-------|
| `sun_mate` | Sun Tzu × Gabor Maté (eine Stimme) | Die Beratungsstimme — mitfühlend + scharf, kein Rollenspiel |
| `ooda` | OODA Loop | Das Tempo — Observe-Orient-Decide-Act |
| `systems` | Systems Thinking | Die Struktur — Feedback-Loops, Hebelpunkte |
| `game_theory` | Spieltheorie | Die Mathematik — Nash, Dominant Strategy, Signaling |
| `context-audit` | Kontextkritische Audit | Findet übersehene Nuancen (versteckte Akteure, Vulnerabilität) |

Jeder Skill teilt dieselbe API (`principles.json`, `schema.json`,
`report_template.md`, 9-Phasen-Pipeline).

## Build

```bash
cargo build
cargo test    # erwartet: 2 passed
```

## Usage

```bash
# Alle 4 Frameworks
albert-strategy-orchestrator \
  --skills sun_mate,ooda,systems,game_theory \
  --mission mission.txt \
  --out consolidated.json

# Nur ein Framework
albert-strategy-orchestrator --skills sun_mate

# Verfügbare Skills auflisten
albert-strategy-orchestrator --list
```

## CLI-Ausgabe

- `Consensus Score` — % Übereinstimmung bei primärer COA
- `Context Dimensions` — kontextkritische Nuancen (z.B. migrationskontext)
- `Future Prediction` — if_we_act / if_we_wait (3/6/12 Monate)

## Skill-Export

Die Strategy-Skills liegen unter `~/.hermes/skills/strategy/` (Teil von
Hermes Agent). Dieses Repo enthält nur den Rust-Orchestrator.

## License

MIT
