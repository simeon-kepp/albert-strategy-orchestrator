//! Consensus/Conflict Engine: vergleicht mehrere StrategyReports und hebt
//! Gemeinsamkeiten + Widersprüche hervor. Erzeugt konsolidiertes Dashboard.
//!
//! Hardening 2026-07-18: die ursprüngliche Version tat so, als wäre "Konsens"
//! ein reiner String-Match auf ein COA-Label — kein Confidence-Gewicht, kein
//! Inhaltsvergleich, `recommended_blend`/`divergences` waren canned Strings.
//! Alles hier ersetzt das mit tatsächlich abgeleiteter Logik; siehe einzelne
//! Funktionskommentare für was konkret vorher fehlte.

use crate::api::StrategyReport;
use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone)]
pub struct ConsensusResult {
    pub n_skills: usize,
    pub all_agree_primary: bool,
    pub primary_coa: HashMap<String, String>,
    pub confidence_levels: HashMap<String, String>,
    /// Konfidenz-gewichteter Score (Standard ab jetzt).
    pub consensus_score: u8,
    /// Der alte, ungewichtete Score (reine Übereinstimmungs-Quote) — bewusst
    /// weiterhin berechnet und ausgewiesen, damit während der Umstellung
    /// sichtbar bleibt, wie stark die Gewichtung das Ergebnis verschiebt.
    pub consensus_score_unweighted: u8,
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

/// Konfidenz-Level -> numerisches Gewicht. Vorher gab es dafür nichts —
/// `confidence_levels` wurde nur als rohe Strings pro Skill gespeichert, nie
/// in irgendeine Berechnung einbezogen. Case-insensitive, deckt DE+EN ab.
fn confidence_to_weight(level: &str) -> f32 {
    match level.to_lowercase().as_str() {
        "high" | "hoch" => 1.0,
        "medium" | "mittel" => 0.6,
        "low" | "niedrig" => 0.3,
        _ => 0.5, // unbekannt/fehlend — weder ignorieren noch übergewichten
    }
}

/// Erste Satz eines Fließtexts, als kurzer Kontext-Auszug für Divergenz-Meldungen.
fn first_sentence(text: &str) -> String {
    let trimmed = text.trim();
    match trimmed.find(['.', '!', '?']) {
        Some(idx) => trimmed[..=idx].to_string(),
        None => trimmed.chars().take(160).collect(),
    }
}

/// Normalisiert einen Theme-String zu einem Token-Set für Jaccard-Vergleich —
/// lowercase, Satzzeichen raus, auf Wörter aufgeteilt.
fn tokenize(theme: &str) -> HashSet<String> {
    theme
        .to_lowercase()
        .chars()
        .map(|c| if c.is_alphanumeric() { c } else { ' ' })
        .collect::<String>()
        .split_whitespace()
        .map(|s| s.to_string())
        .collect()
}

fn jaccard(a: &HashSet<String>, b: &HashSet<String>) -> f32 {
    if a.is_empty() && b.is_empty() {
        return 1.0;
    }
    let intersection = a.intersection(b).count() as f32;
    let union = a.union(b).count() as f32;
    if union == 0.0 {
        0.0
    } else {
        intersection / union
    }
}

const THEME_SIMILARITY_THRESHOLD: f32 = 0.6;

/// Fuzzy-Merge statt exaktem String-Dedupe: zwei unterschiedlich formulierte,
/// aber inhaltlich gleiche Themes (z.B. "diaspora leverage" vs.
/// "Diaspora-Hebelwirkung") wurden vorher NIE zusammengeführt, weil die alte
/// Version ein reines `BTreeSet<String>` war. Hier: Token-Set-Jaccard-
/// Ähnlichkeit gruppiert Varianten, die längste/detaillierteste Formulierung
/// wird als Kanonisch-Text behalten.
fn merge_similar_themes(raw: Vec<(String, String)>) -> Vec<String> {
    let mut clusters: Vec<(HashSet<String>, String, HashSet<String>)> = Vec::new();
    // (tokens, canonical_text, contributing_skill_ids) — skill_ids aktuell nur
    // zur Nachvollziehbarkeit mitgeführt, nicht separat ausgegeben (das Feld
    // bleibt Vec<String> nach außen, um die bestehende API nicht zu brechen).

    for (skill_id, theme) in raw {
        let tokens = tokenize(&theme);
        let mut merged_into_existing = false;
        for (cluster_tokens, canonical, contributors) in clusters.iter_mut() {
            if jaccard(cluster_tokens, &tokens) >= THEME_SIMILARITY_THRESHOLD {
                if theme.len() > canonical.len() {
                    *canonical = theme.clone();
                }
                contributors.insert(skill_id.clone());
                merged_into_existing = true;
                break;
            }
        }
        if !merged_into_existing {
            let mut contributors = HashSet::new();
            contributors.insert(skill_id.clone());
            clusters.push((tokens, theme, contributors));
        }
    }

    let mut out: Vec<String> = clusters.into_iter().map(|(_, text, _)| text).collect();
    out.sort();
    out
}

/// Echte Per-Skill-Divergenz statt einer 2-Varianten-Konserve. Für jedes Paar
/// mit unterschiedlicher primärer COA: konkrete Zeile mit beiden Skill-IDs,
/// beiden COA-IDs, und einem Reasoning-Auszug je Seite.
///
/// Eine fruehere Version dieser Funktion flaggte zusaetzlich Skill-Paare, die
/// auf derselben COA landen, aber keine gemeinsamen
/// `strategic_principles_applied`-IDs zitieren, als "zufaellige
/// Uebereinstimmung". Das erwies sich im Dry-Run gegen echte Case-Daten als
/// strukturell nutzlos: die 4 Frameworks haben *per Design* vollstaendig
/// getrennte Prinzipien-Vokabulare (sun_mate zitiert nie eine OODA-Prinzip-ID
/// und umgekehrt) — die Bedingung feuerte deshalb bei JEDEM einzigen Paar,
/// unabhaengig davon, ob die Begruendungen inhaltlich zusammenhingen oder
/// nicht. Reines Rauschen, keine Information. Entfernt statt "gefixt", weil
/// es keine sinnvolle Schwelle gibt, die dieses Setup unterscheiden koennte.
fn compute_divergences(skills: &[StrategyReport]) -> Vec<String> {
    let mut lines = Vec::new();

    for i in 0..skills.len() {
        for j in (i + 1)..skills.len() {
            let a = &skills[i];
            let b = &skills[j];
            let coa_a = extract_primary_coa(a);
            let coa_b = extract_primary_coa(b);
            if coa_a != coa_b {
                lines.push(format!(
                    "{} empfiehlt {} ({}); {} empfiehlt {} ({}) — Kernkonflikt.",
                    a.skill_id,
                    coa_a,
                    first_sentence(&a.report.reasoning),
                    b.skill_id,
                    coa_b,
                    first_sentence(&b.report.reasoning),
                ));
            }
        }
    }

    if lines.is_empty() {
        lines.push(
            "Keine Divergenzen: alle Frameworks stimmen bei primärer COA überein.".into(),
        );
    }
    lines
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
    let consensus_score_unweighted = if n == 0 {
        0
    } else {
        ((agree_count as f32 / n as f32) * 100.0).round() as u8
    };

    let total_weight: f32 = skills
        .iter()
        .map(|s| confidence_to_weight(&s.report.confidence_assessment.level))
        .sum();
    let agree_weight: f32 = skills
        .iter()
        .filter(|s| Some(&extract_primary_coa(s)) == first_primary.as_ref())
        .map(|s| confidence_to_weight(&s.report.confidence_assessment.level))
        .sum();
    let consensus_score = if total_weight <= 0.0 {
        0
    } else {
        ((agree_weight / total_weight) * 100.0).round() as u8
    };

    // recommended_blend: vorher ein hartkodierter String, der sogar einen
    // toten Skill-Namen ("sun_tzu") referenzierte. Jetzt aus den tatsächlich
    // zustimmenden/abweichenden Skill-IDs abgeleitet.
    let agreeing: Vec<&str> = skills
        .iter()
        .filter(|s| Some(&extract_primary_coa(s)) == first_primary.as_ref())
        .map(|s| s.skill_id.as_str())
        .collect();
    let disagreeing: Vec<&str> = skills
        .iter()
        .filter(|s| Some(&extract_primary_coa(s)) != first_primary.as_ref())
        .map(|s| s.skill_id.as_str())
        .collect();
    let recommended_blend = if all_agree {
        format!("{} — einstimmig", agreeing.join(" + "))
    } else if disagreeing.is_empty() {
        agreeing.join(" + ")
    } else {
        format!(
            "{} (+ {} als Tempo-/Kontext-Layer)",
            agreeing.join(" + "),
            disagreeing.join(", ")
        )
    };

    // Cross-Framework Themes: fuzzy statt exaktem String-Dedupe (siehe
    // merge_similar_themes).
    let raw_themes: Vec<(String, String)> = skills
        .iter()
        .flat_map(|s| {
            s.cross_framework_themes
                .iter()
                .map(move |t| (s.skill_id.clone(), t.clone()))
        })
        .collect();
    let cross_framework_themes = merge_similar_themes(raw_themes);

    let divergences = compute_divergences(skills);

    // Context Dimensions: Konflikte werden jetzt geflaggt statt lautlos vom
    // ersten Skill "gewonnen". Sammle ALLE Werte pro Key; wenn sie
    // übereinstimmen, wie vorher direkt speichern, sonst als
    // {"conflict": true, "values_by_skill": {...}} markieren.
    let mut all_values: HashMap<String, Vec<(String, serde_json::Value)>> = HashMap::new();
    for s in skills {
        if let serde_json::Value::Object(map) = &s.context_dimensions {
            for (k, v) in map {
                all_values
                    .entry(k.clone())
                    .or_default()
                    .push((s.skill_id.clone(), v.clone()));
            }
        }
    }
    let mut context_dims: HashMap<String, serde_json::Value> = HashMap::new();
    for (k, values) in all_values {
        let first_val = &values[0].1;
        let all_equal = values.iter().all(|(_, v)| v == first_val);
        if all_equal {
            context_dims.insert(k, first_val.clone());
        } else {
            let values_by_skill: serde_json::Map<String, serde_json::Value> =
                values.into_iter().collect();
            context_dims.insert(
                k,
                serde_json::json!({
                    "conflict": true,
                    "values_by_skill": serde_json::Value::Object(values_by_skill),
                }),
            );
        }
    }

    ConsensusResult {
        n_skills: n,
        all_agree_primary: all_agree,
        primary_coa,
        confidence_levels,
        consensus_score,
        consensus_score_unweighted,
        recommended_blend,
        cross_framework_themes,
        divergences,
        context_dimensions: serde_json::Value::Object(context_dims.into_iter().collect()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::api::*;

    fn dummy(skill_id: &str, primary: &str, conf: &str) -> StrategyReport {
        dummy_full(skill_id, primary, conf, "x", &[])
    }

    fn dummy_full(
        skill_id: &str,
        primary: &str,
        conf: &str,
        reasoning: &str,
        principles: &[&str],
    ) -> StrategyReport {
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
                reasoning: reasoning.into(),
                strategic_principles_applied: principles.iter().map(|s| s.to_string()).collect(),
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
            dummy("sun_mate", "COA-A", "medium"),
            dummy("ooda", "COA-A", "medium"),
            dummy("systems", "COA-A", "medium"),
        ];
        let c = resolve(&reports);
        assert!(c.all_agree_primary);
        assert_eq!(c.consensus_score, 100);
        assert_eq!(c.consensus_score_unweighted, 100);
        assert_eq!(c.cross_framework_themes.len(), 2);
        assert!(c.recommended_blend.contains("einstimmig"));
        assert!(!c.recommended_blend.contains("sun_tzu")); // toter Skill-Name muss weg sein
    }

    #[test]
    fn confidence_weighting_shifts_score_below_unweighted() {
        // 2 von 3 stimmen überein (unweighted = 67%), aber der eine
        // abweichende hat "high" confidence, die beiden übereinstimmenden nur
        // "low" — der gewichtete Score muss dadurch NIEDRIGER als 67 liegen.
        let reports = vec![
            dummy("sun_mate", "COA-A", "low"),
            dummy("ooda", "COA-A", "low"),
            dummy("systems", "COA-B", "high"),
        ];
        let c = resolve(&reports);
        assert_eq!(c.consensus_score_unweighted, 67);
        assert!(c.consensus_score < c.consensus_score_unweighted);
    }

    #[test]
    fn divergence_detail_names_both_skills_and_coas() {
        let reports = vec![
            dummy_full("sun_mate", "COA-A", "high", "Vermieter-Achse ist der Hebel.", &["p1"]),
            dummy_full("game_theory", "COA-C", "high", "Signaling braucht Commitment.", &["p2"]),
        ];
        let c = resolve(&reports);
        assert_eq!(c.divergences.len(), 1);
        assert!(c.divergences[0].contains("sun_mate"));
        assert!(c.divergences[0].contains("game_theory"));
        assert!(c.divergences[0].contains("COA-A"));
        assert!(c.divergences[0].contains("COA-C"));
    }

    #[test]
    fn same_coa_different_principles_is_not_flagged_as_divergence() {
        // Regression: eine fruehere Version flaggte dies als "zufaellige
        // Uebereinstimmung", was bei diesem System (4 Frameworks mit
        // absichtlich disjunkten Prinzipien-Vokabularen) immer feuerte und
        // damit nutzlos war. Gleiche COA + unterschiedliche Prinzipien-IDs
        // ist hier der Normalfall, keine Divergenz.
        let reports = vec![
            dummy_full("sun_mate", "COA-A", "high", "x", &["preserve_resources"]),
            dummy_full("ooda", "COA-A", "high", "x", &["disorient"]),
        ];
        let c = resolve(&reports);
        assert_eq!(c.divergences.len(), 1);
        assert!(c.divergences[0].contains("Keine Divergenzen"));
    }

    #[test]
    fn fuzzy_theme_merge_collapses_reworded_duplicates() {
        let mut a = dummy("sun_mate", "COA-A", "high");
        a.cross_framework_themes = vec!["Gesamtschau statt Isolation".into()];
        let mut b = dummy("ooda", "COA-A", "high");
        b.cross_framework_themes = vec!["Isolation statt Gesamtschau betrachten".into()];
        let c = resolve(&[a, b]);
        // Beide Themes teilen genug Tokens ("gesamtschau", "isolation", "statt"),
        // um in einen Cluster zu fallen statt als 2 separate Einträge zu erscheinen.
        assert_eq!(c.cross_framework_themes.len(), 1);
    }

    #[test]
    fn context_dimension_conflict_is_flagged_not_silently_overwritten() {
        let mut a = dummy("sun_mate", "COA-A", "high");
        a.context_dimensions = serde_json::json!({"migrationskontext": {"befund": "A"}});
        let mut b = dummy("ooda", "COA-A", "high");
        b.context_dimensions = serde_json::json!({"migrationskontext": {"befund": "B"}});
        let c = resolve(&[a, b]);
        let dim = &c.context_dimensions["migrationskontext"];
        assert_eq!(dim["conflict"], serde_json::Value::Bool(true));
        assert!(dim["values_by_skill"]["sun_mate"].is_object());
        assert!(dim["values_by_skill"]["ooda"].is_object());
    }
}
