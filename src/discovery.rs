//! Skill discovery: lädt verfügbare Strategy-Skills aus ~/.hermes/skills/strategy/.
//! Jeder Skill-Ordner hat principles.json (Metadaten + Prinzipien) und schema.json (API).

use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::PathBuf;

#[derive(Debug, Clone, Deserialize)]
pub struct Principle {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub summary: String,
    #[serde(default)]
    pub applies_when: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SkillMeta {
    pub skill_id: String,
    pub display_name: String,
    #[serde(default)]
    pub version: String,
    #[serde(default)]
    pub framework_source: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub axioms: Vec<String>,
    #[serde(default)]
    pub avoid: Vec<String>,
    #[serde(default)]
    pub principles: Vec<Principle>,
    #[serde(default)]
    pub metrics: serde_json::Value,
}

pub fn strategy_dir() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/home/eri-irfos".into());
    PathBuf::from(home).join(".hermes/skills/strategy")
}

/// Listet alle verfügbaren Skills (Ordner mit principles.json).
pub fn discover_skills() -> Result<Vec<(String, SkillMeta)>> {
    let dir = strategy_dir();
    let mut out = Vec::new();
    if !dir.exists() {
        return Ok(out);
    }
    for entry in std::fs::read_dir(&dir).context("read strategy dir")? {
        let entry = entry?;
        if !entry.path().is_dir() {
            continue;
        }
        let pid = entry.path().join("principles.json");
        if !pid.exists() {
            continue;
        }
        let meta: SkillMeta = serde_json::from_str(
            &std::fs::read_to_string(&pid).context("read principles.json")?,
        )
        .context("parse principles.json")?;
        out.push((meta.skill_id.clone(), meta));
    }
    out.sort_by(|a, b| a.0.cmp(&b.0));
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn discovers_three_skills() {
        let skills = discover_skills().unwrap();
        let ids: Vec<&str> = skills.iter().map(|(id, _)| id.as_str()).collect();
        assert!(ids.contains(&"sun_mate"));
        assert!(ids.contains(&"ooda"));
        assert!(ids.contains(&"systems"));
    }
}
