//! albert strategy --skills sun_mate,ooda,systems,game_theory --mission mission.txt [--out report.json]
//!
//! Multi-Framework Strategy Orchestrator. Laedt die gewaehlten Skills aus
//! ~/.hermes/skills/strategy/<id>/, validiert die Skill-Reports gegen schema.json,
//! fuehrt die Consensus-Engine aus und schreibt einen konsolidierten Report.

mod api;
mod consensus;
mod discovery;

use anyhow::{Context, Result};
use clap::Parser;
use std::path::PathBuf;

use api::StrategyReport;
use consensus::ConsensusResult;

#[derive(Parser, Debug)]
#[command(name = "albert-strategy", about = "Multi-framework strategy orchestrator (sun_mate, ooda, systems, game_theory, ...)")]
struct Cli {
    /// Komma-getrennte Liste der Skills, z.B. "sun_mate,ooda,systems".
    /// "all" = alle verfügbaren Skills dynamisch laden.
    #[arg(long, value_delimiter = ',', default_value = "all")]
    skills: Vec<String>,

    /// Pfad zur Missions-Datei (Text/JSON). Wenn fehlend: stdin.
    #[arg(long)]
    mission: Option<PathBuf>,

    /// Ausgabe-Pfad fuer den konsolidierten JSON-Report.
    #[arg(long)]
    out: Option<PathBuf>,

    /// Nur verfuegbare Skills auflisten.
    #[arg(long)]
    list: bool,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    if cli.list {
        let skills = discovery::discover_skills()?;
        println!("Verfuegbare Strategy-Skills:");
        for (id, meta) in &skills {
            println!("  {}  —  {} v{}", id, meta.display_name, meta.version);
            println!("        {}", meta.description);
        }
        return Ok(());
    }

    // 1) Skills aufloesen
    let available = discovery::discover_skills()?;
    let avail_map: std::collections::HashMap<&str, &discovery::SkillMeta> =
        available.iter().map(|(id, m)| (id.as_str(), m)).collect();

    // "all" = alle verfuegbaren Skills dynamisch
    let cli_skills: Vec<String> = if cli.skills == vec!["all"] {
        available.iter().map(|(id, _)| id.clone()).collect()
    } else {
        cli.skills.clone()
    };

    let mut chosen = Vec::new();
    for s in &cli_skills {
        match avail_map.get(s.as_str()) {
            Some(m) => chosen.push((s.clone(), (*m).clone())),
            None => anyhow::bail!(
                "Skill '{}' nicht gefunden unter ~/.hermes/skills/strategy/",
                s
            ),
        }
    }
    if chosen.is_empty() {
        anyhow::bail!("Keine gueltigen Skills gewaehlt.");
    }

    println!("Running {} strategic frameworks...", chosen.len());
    for (id, meta) in &chosen {
        println!("  {} ({})...", id, meta.display_name);
    }

    // 2) Mission laden
    let mission_text = match &cli.mission {
        Some(p) => std::fs::read_to_string(p).context("read mission file")?,
        None => {
            use std::io::Read;
            let mut buf = String::new();
            std::io::stdin().read_to_string(&mut buf)?;
            buf
        }
    };
    println!("Mission geladen ({} Zeichen).", mission_text.len());

    // Case-Verzeichnis = der Ordner, in dem die Mission-Datei selbst liegt (per
    // Konvention <case_root>/case/mission_*.txt). Vorher war dieser Pfad hart auf
    // Lauras Ordner verdrahtet, unabhaengig davon, welche --mission tatsaechlich
    // uebergeben wurde — pipeline.sh/call_the_swat.sh wurden bereits parametrisiert,
    // aber diese Rust-Binary hat das nie mitbekommen. Faellt ohne --mission (stdin-
    // Modus) auf Lauras Fall zurueck, fuer Abwaertskompatibilitaet.
    let case_dir: PathBuf = match &cli.mission {
        Some(p) => p.parent().map(|d| d.to_path_buf()).unwrap_or_else(|| {
            PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| "/home/eri-irfos".into()))
                .join("Desktop/do it for laura /case")
        }),
        None => PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| "/home/eri-irfos".into()))
            .join("Desktop/do it for laura /case"),
    };

    // 3) Skill-Reports laden
    let reports = load_reports_for(&cli_skills, &case_dir)?;

    // 4) Jeden Report gegen schema.json validieren
    for r in &reports {
        validate_against_schema(r)?;
    }
    println!(
        "Alle {} Skill-Reports gegen schema.json validiert ✓",
        reports.len()
    );

    // 5) Consensus Engine
    let consensus = consensus::resolve(&reports);
    println!(
        "Consensus Score: {}%  |  alle primaer = {}",
        consensus.consensus_score, consensus.all_agree_primary
    );

    // future_prediction wurde vorher NUR fuer die stdout-Zusammenfassung
    // (print_summary, find_map -> erster nicht-null Treffer) berechnet, aber
    // nie in die persistierte --out-Datei geschrieben — beim Speichern gingen
    // alle 4 Perspektiven-Prognosen stillschweigend verloren. Jetzt als Map
    // ueber alle Skills, die tatsaechlich eine future_prediction geliefert
    // haben (nicht nur die erste gefundene).
    let future_predictions_by_skill: std::collections::HashMap<String, serde_json::Value> =
        reports
            .iter()
            .filter(|r| r.future_prediction.is_object())
            .map(|r| (r.skill_id.clone(), r.future_prediction.clone()))
            .collect();

    // 6) Konsolidierten Report schreiben
    let consolidated = serde_json::json!({
        "n_skills": consensus.n_skills,
        "consensus_score": consensus.consensus_score,
        "consensus_score_unweighted": consensus.consensus_score_unweighted,
        "all_agree_primary": consensus.all_agree_primary,
        "primary_coa": consensus.primary_coa,
        "confidence_levels": consensus.confidence_levels,
        "recommended_blend": consensus.recommended_blend,
        "cross_framework_themes": consensus.cross_framework_themes,
        "divergences": consensus.divergences,
        "context_dimensions": consensus.context_dimensions,
        "future_predictions_by_skill": future_predictions_by_skill,
        "skills": reports,
        "failure_register": load_failure_register(&case_dir),
    });

    match &cli.out {
        Some(p) => {
            std::fs::write(p, serde_json::to_string_pretty(&consolidated)?)
                .context("write out file")?;
            println!("Konsolidierter Report -> {}", p.display());
        }
        None => {
            println!("\n=== KONSOLIDIERTER REPORT ===");
            println!("{}", serde_json::to_string_pretty(&consolidated)?);
        }
    }

    print_summary(&consensus, &reports, &case_dir);
    Ok(())
}

/// Laedt die Skill-Reports. Test-Implementierung: liest die echten Analyse-JSONs
/// aus dem Laura-Ordner (desktop/do it for laura /<skill>_analysis.json).
fn load_reports_for(skills: &[String], base: &std::path::Path) -> Result<Vec<StrategyReport>> {
    let mut out = Vec::new();
    for s in skills {
        // Bevorzuge generic Version (falls vorhanden)
        let generic = base.join(format!("{}_analysis_generic.json", s));
        let legacy = base.join(format!("{}_analysis.json", s));
        let p = if generic.exists() { generic } else { legacy };
        if !p.exists() {
            anyhow::bail!(
                "Kein Analyse-JSON fuer '{}' unter {} — Pipeline zuerst im Agent ausfuehren.",
                s,
                base.display()
            );
        }
        let mut r: StrategyReport =
            serde_json::from_str(&std::fs::read_to_string(&p)?).context("parse analysis json")?;
        // r.cross_framework_themes ist bereits aus der ersten Deserialisierung
        // korrekt befuellt (StrategyReport hat das Feld direkt) — der vorherige
        // zweite Roh-Read derselben Datei nur zur erneuten Extraktion war totes,
        // dupliziertes I/O.
        r.detailed_strategies = r.report.detailed_strategies.clone();
        r.future_prediction = r.report.future_prediction.clone();
        r.context_dimensions = r.analysis.context_dimensions.clone();
        out.push(r);
    }
    Ok(out)
}

/// Laedt das failure_register.json aus dem Case-Verzeichnis (4. Sektion des Reports).
fn load_failure_register(base: &std::path::Path) -> serde_json::Value {
    let p = base.join("failure_register.json");
    match std::fs::read_to_string(&p) {
        Ok(t) => serde_json::from_str(&t).unwrap_or(serde_json::Value::Null),
        Err(_) => serde_json::Value::Null,
    }
}

/// Structural validation gegen das standardisierte Schema (Pflichtfelder).
fn validate_against_schema(r: &StrategyReport) -> Result<()> {
    if r.skill_id.is_empty() {
        anyhow::bail!("skill_id fehlt");
    }
    if r.report.executive_summary.is_empty() {
        anyhow::bail!("report.executive_summary fehlt");
    }
    if r.report.recommended_strategy.is_empty() {
        anyhow::bail!("report.recommended_strategy fehlt");
    }
    if r.analysis.phase4_intelligence_assessment.known_facts.is_empty() {
        anyhow::bail!("phase4.known_facts leer");
    }
    if r.report.strategic_principles_applied.is_empty() {
        anyhow::bail!("strategic_principles_applied leer");
    }
    // The remaining required fields per schema.json (report.reasoning, .decision_points,
    // .implementation_steps, .warning_signs, .fallback_plans, .confidence_assessment) were
    // previously never checked here at all — a skill whose output JSON silently drifted from
    // its own schema.json (wrong field names, missing keys) passed validation every time
    // because #[serde(default)] quietly fills empty string/Vec/struct defaults for anything
    // missing, and this function never looked at those fields to notice. That's exactly how
    // game_theory_analysis_generic.json shipped with an entirely empty report section for
    // months without a single error. Check them for real now.
    if r.report.reasoning.is_empty() {
        anyhow::bail!("report.reasoning fehlt ({})", r.skill_id);
    }
    if r.report.decision_points.is_empty() {
        anyhow::bail!("report.decision_points leer ({})", r.skill_id);
    }
    if r.report.confidence_assessment.level.is_empty() {
        anyhow::bail!("report.confidence_assessment.level fehlt ({})", r.skill_id);
    }
    // Diese 3 waren im obigen Kommentar seit 2026-07-18 als "jetzt geprueft"
    // dokumentiert, aber nie tatsaechlich implementiert — nur reasoning,
    // decision_points und confidence_assessment.level bekamen echte Checks.
    // Genau die Luecke, die den game_theory-Vorfall ermoeglicht hat, war also
    // fuer implementation_steps/warning_signs/fallback_plans noch offen.
    if r.report.implementation_steps.is_empty() {
        anyhow::bail!("report.implementation_steps leer ({})", r.skill_id);
    }
    if r.report.warning_signs.is_empty() {
        anyhow::bail!("report.warning_signs leer ({})", r.skill_id);
    }
    if r.report.fallback_plans.is_empty() {
        anyhow::bail!("report.fallback_plans leer ({})", r.skill_id);
    }
    Ok(())
}

fn print_summary(c: &ConsensusResult, reports: &[StrategyReport], case_dir: &std::path::Path) {
    println!("\n=== MISSION SCORECARD (Consensus) ===");
    println!("Skills            : {}", c.n_skills);
    println!("Consensus Score   : {}%", c.consensus_score);
    println!("All Agree Primary : {}", c.all_agree_primary);
    println!("Recommended Blend : {}", c.recommended_blend);
    println!("Confidence        : {:?}", c.confidence_levels.values().collect::<Vec<_>>());
    println!("Themes (>=2 FW)   : {}", c.cross_framework_themes.len());
    for t in &c.cross_framework_themes {
        println!("  + {}", t);
    }
    // Context Dimensions
    if let serde_json::Value::Object(map) = &c.context_dimensions {
        if !map.is_empty() {
            println!("\nContext Dimensions (kontextkritisch):");
            for k in map.keys() {
                println!("  • {}", k);
            }
        }
    }
    // Failure Register
    if let Some(fp) = load_failure_register(case_dir).get("eintraege") {
        if let Some(arr) = fp.as_array() {
            println!("\nVersagens-Register: {} Eintraege", arr.len());
        }
    }
    if let Some(fp) = reports.iter().find_map(|r| {
        if r.future_prediction.is_object() {
            Some(&r.future_prediction)
        } else {
            None
        }
    }) {
        println!(
            "\nFuture Prediction (aus {}):",
            reports
                .iter()
                .find(|r| r.future_prediction.is_object())
                .map(|r| r.skill_id.clone())
                .unwrap_or_default()
        );
        if let Some(act) = fp.get("if_we_act").and_then(|v| v.as_array()) {
            for s in act {
                if let (Some(h), Some(sc)) = (s.get("horizon"), s.get("scenario")) {
                    println!(
                        "  [act {}] {}",
                        h,
                        sc.as_str().unwrap_or("").chars().take(60).collect::<String>()
                    );
                }
            }
        }
        if let Some(wait) = fp.get("if_we_wait").and_then(|v| v.as_array()) {
            if let Some(s) = wait.last() {
                if let (Some(h), Some(sc)) = (s.get("horizon"), s.get("scenario")) {
                    println!(
                        "  [wait {}] {}",
                        h,
                        sc.as_str().unwrap_or("").chars().take(60).collect::<String>()
                    );
                }
            }
        }
    }
}
