//! Consensus/Conflict Engine: vergleicht mehrere StrategyReports und hebt
//! Gemeinsamkeiten + Widersprüche hervor. Erzeugt konsolidiertes Dashboard.

use crate::api::StrategyReport;
use std::collections::{HashMap, BTreeSet};

#[derive(Debug, Clone)]
pub struct ConsensusResult {
    pub n_skills: usize,
    pub all_agree_primary: bool,
    pub primary_coa: HashMap<String, String>,
    pub confidence_levels: HashMap<String, String>,
    pub consensus_score: u8,
    pub recommended_blend: String,
    pub cross_framework_themes: Vec<String>,
    pub divergences: Vec<String>,
    pub context_dimensions: serde_json::Value,
}

/// Extrahiert die primäre COA-ID aus "recommended_strategy" (z.B. "COA-A primär..." -> "COA-A").
fn extract_primary_coa(report: &StrategyReport) -> String {
    let s = &report.report.recommended_strategy;
    if let Some(rest) = s.strip_prefix("COA-") {
        let end = rest
            .find(|c: char| !c.is_alphanumeric())
            .unwrap_or(rest.len());
        format!("COA-{}", &rest[..end])
    } else {
        "UNKNOWN".into()
    }
}

pub fn resolve(skills: &[StrategyReport]) -> ConsensusResult {
    let n = skills.len();
    let mut primary_coa = HashMap::new();
    let mut confidence_levels = HashMap::new();

    for s in skills {
        primary_coa.insert(s.skill_id.clone(), extract_primary_coa(s));
        confidence_levels.insert(
            s.skill_id.clone(),
            s.report.confidence_assessment.level.clone(),
        );
    }

    let first_primary = skills.first().map(extract_primary_coa);
    let all_agree = skills
        .iter()
        .all(|s| Some(&extract_primary_coa(s)) == first_primary.as_ref());

    let agree_count = skills
        .iter()
        .filter(|s| Some(&extract_primary_coa(s)) == first_primary.as_ref())
        .count();
    let consensus_score = if n == 0 {
        0
    } else {
        ((agree_count as f32 / n as f32) * 100.0).round() as u8
    };

    let recommended_blend = if all_agree {
        "sun_tzu + systems (+ ooda tempo-layer)".into()
    } else {
        "frameworke-spezifisch — Diversität erfordert manuelle Synthese".into()
    };

    // Cross-Framework Themes: jedes Skill-JSON liefert `cross_framework_themes`
    // (framework-übergreifend identisch formuliert). Union + Dedupe.
    let mut theme_set: BTreeSet<String> = BTreeSet::new();
    for s in skills {
        for t in &s.cross_framework_themes {
            theme_set.insert(t.clone());
        }
    }
    let cross_framework_themes: Vec<String> = theme_set.into_iter().collect();

    let divergences = if all_agree {
        vec!["Gering: alle Frameworks empfehlen dieselbe primäre COA.".into()]
    } else {
        vec!["Frameworke divergieren bei primärer COA — manuelle Synthese nötig.".into()]
    };

    // Context Dimensions: aggregiere aus allen Skills (Migrationskontext etc.)
    let mut context_dims: HashMap<String, serde_json::Value> = HashMap::new();
    for s in skills {
        if let serde_json::Value::Object(map) = &s.context_dimensions {
            for (k, v) in map {
                context_dims.entry(k.clone()).or_insert_with(|| v.clone());
            }
        }
    }

    ConsensusResult {
        n_skills: n,
        all_agree_primary: all_agree,
        primary_coa,
        confidence_levels,
        consensus_score,
        recommended_blend,
        cross_framework_themes,
        divergences,
        context_dimensions: serde_json::Value::Object(
            context_dims.into_iter().collect()
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::api::*;

    fn dummy(skill_id: &str, primary: &str, conf: &str) -> StrategyReport {
        StrategyReport {
            skill_id: skill_id.into(),
            framework_version: "1.0.0".into(),
            mission: Mission {
                objective: "x".into(),
                end_state: "x".into(),
                ..Default::default()
            },
            analysis: Analysis::default(),
            report: Report {
                executive_summary: "x".into(),
                recommended_strategy: format!("{} primär", primary),
                reasoning: "x".into(),
                confidence_assessment: ConfidenceAssessment {
                    level: conf.into(),
                    basis: "x".into(),
                },
                ..Default::default()
            },
            metrics: serde_json::Value::Null,
            sources: vec![],
            cross_framework_themes: vec!["A".into(), "B".into()],
            detailed_strategies: serde_json::Value::Null,
            future_prediction: serde_json::Value::Null,
            context_dimensions: serde_json::Value::Null,
        }
    }

    #[test]
    fn all_agree_gives_100() {
        let reports = vec![
            dummy("sun_tzu", "COA-A", "medium"),
            dummy("ooda", "COA-A", "medium"),
            dummy("systems", "COA-A", "medium"),
        ];
        let c = resolve(&reports);
        assert!(c.all_agree_primary);
        assert_eq!(c.consensus_score, 100);
        assert_eq!(c.cross_framework_themes.len(), 2);
    }
}
