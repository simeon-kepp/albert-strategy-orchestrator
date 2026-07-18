//! Standardized StrategySkill API — Rust-Pendant zu schema.json.
//! Jeder Skill (sun_tzu, ooda, systems, ...) liefert exakt diese Struktur.
//! Der Orchestrator behandelt alle Skills gleich.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
pub struct Mission {
    pub objective: String,
    pub end_state: String,
    #[serde(default)]
    pub success_criteria: Vec<String>,
    #[serde(default)]
    pub failure_criteria: Vec<String>,
    #[serde(default)]
    pub constraints: Vec<String>,
    #[serde(default)]
    pub unknowns: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
pub struct IntelligenceAssessment {
    #[serde(default)]
    pub known_facts: Vec<String>,
    #[serde(default)]
    pub assumptions: Vec<String>,
    #[serde(default)]
    pub unknowns: Vec<String>,
    #[serde(default)]
    pub missing_intelligence: Vec<String>,
    #[serde(default)]
    pub confidence_per_conclusion: serde_json::Value,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
pub struct CourseOfAction {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub advantages: Vec<String>,
    #[serde(default)]
    pub disadvantages: Vec<String>,
    #[serde(default)]
    pub required_resources: Vec<String>,
    pub risk: String,
    #[serde(default)]
    pub expected_resistance: String,
    pub chance_of_success: String,
    #[serde(default)]
    pub time_horizon: String,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
pub struct Analysis {
    #[serde(default)]
    pub phase1_mission_definition: serde_json::Value,
    #[serde(default)]
    pub phase2_battlefield_mapping: serde_json::Value,
    #[serde(default)]
    pub phase3_terrain_analysis: serde_json::Value,
    #[serde(default)]
    pub phase4_intelligence_assessment: IntelligenceAssessment,
    #[serde(default)]
    pub phase5_strategic_principles: serde_json::Value,
    #[serde(default)]
    pub phase6_courses_of_action: Vec<CourseOfAction>,
    #[serde(default)]
    pub phase7_counter_strategy: serde_json::Value,
    /// Steelman gegen die eigene primaere Empfehlung (Phase 7b, Hardening
    /// 2026-07-18) — optional/#[serde(default)] waehrend des Rollouts, noch
    /// nicht in validate_against_schema hart geprueft.
    #[serde(default)]
    pub phase7b_self_critique: serde_json::Value,
    #[serde(default)]
    pub phase8_optimization: serde_json::Value,
    #[serde(default)]
    pub phase9_final_recommendation: serde_json::Value,
    #[serde(default)]
    pub context_dimensions: serde_json::Value,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
pub struct ConfidenceAssessment {
    pub level: String,
    #[serde(default)]
    pub basis: String,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
pub struct Report {
    #[serde(default)]
    pub executive_summary: String,
    #[serde(default)]
    pub recommended_strategy: String,
    #[serde(default)]
    pub reasoning: String,
    #[serde(default)]
    pub implementation_steps: Vec<String>,
    #[serde(default)]
    pub decision_points: Vec<String>,
    #[serde(default)]
    pub warning_signs: Vec<String>,
    #[serde(default)]
    pub fallback_plans: Vec<String>,
    #[serde(default)]
    pub strategic_principles_applied: Vec<String>,
    #[serde(default)]
    pub confidence_assessment: ConfidenceAssessment,
    #[serde(default)]
    pub detailed_strategies: serde_json::Value,
    #[serde(default)]
    pub future_prediction: serde_json::Value,
    /// Nur bei Pass-2 (Debatten-Runde) befuellt — Reaktion auf die anderen 3
    /// Frameworks' Pass-1-Positionen (Hardening 2026-07-18). Optional/
    /// #[serde(default)], leer bei Pass-1-only Laeufen.
    #[serde(default)]
    pub debate_response: serde_json::Value,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct StrategyReport {
    pub skill_id: String,
    #[serde(default)]
    pub framework_version: String,
    pub mission: Mission,
    pub analysis: Analysis,
    pub report: Report,
    #[serde(default)]
    pub metrics: serde_json::Value,
    #[serde(default)]
    pub sources: Vec<String>,
    #[serde(default)]
    pub cross_framework_themes: Vec<String>,
    #[serde(default)]
    pub detailed_strategies: serde_json::Value,
    #[serde(default)]
    pub future_prediction: serde_json::Value,
    #[serde(default)]
    pub context_dimensions: serde_json::Value,
}
