#!/usr/bin/env python3
"""
analyze.py — Generic analysis entry-point for a strategy skill.

Nimmt OBEN irgendeine Problemstellung (Prompt/Textdatei) und
produziert a generisches Analyse-JSON im Standard-Format
(siehe schema.json). Domän-agnostisch: funktioniert für jede
Problemstellung, nicht nur den Testfall.

Die 4 Skills (sun_mate, ooda, systems, game_theory) nutzen
dieses selbe Skript mit skill-spezifischer Prinzipien-Datei.

Usage:
  python3 analyze.py <problemstellung.txt> <output.json> [--skill sun_mate]
"""
import sys
import json
import pathlib
import datetime


# Generische Prinzipien pro Skill (domän-agnostisch formuliert)
SKILL_PRINCIPLES = {
    "sun_mate": [
        "Hebel suchen, der die Gesamtsituation verschiebt ohne eigene Exposition",
        "Den höchsten Gewinn ohne offenen Konflikt anstreben",
        "Position fragen, nicht moralisch: wer steht wo, wer hat Macht",
        "Dokumentation so dicht machen, dass Institution reagieren muss",
    ],
    "ooda": [
        "Tempo: schneller orientieren/handeln als der Gegner",
        "Entscheidungszyklus: Observe-Orient-Decide-Act",
        "Überhastung vermeiden (eigene Fehler)",
        "Tempovorteil nutzen um Agenda zu diktieren",
    ],
    "systems": [
        "Fall als vernetztes System, nicht Einzelfall",
        "Rückkopplungsschleifen identifizieren",
        "Hebelpunkt außerhalb der offensichtlichen Arena suchen",
        "Struktur ändern, nicht nur Symptom bekämpfen",
    ],
    "game_theory": [
        "Fall als wiederholtes Spiel zwischen Akteuren",
        "Dominante Strategie bestimmen",
        "Gleichgewicht über Koordinationspunkt verschieben",
        "Institution als Spieler mit Status-quo-Präferenz modellieren",
    ],
}


def analyze(mission: str, skill_id: str) -> dict:
    """Produziert generisches Analyse-JSON.

    HINWEIS: Dieses Skript ist der GENERIC-Einstiegspunkt.
    Die tatsächliche Analyse-Tiefe (Quellen, Fakten, COAs) wird
    vom Agent im Kontext des jeweiligen Falles gefüllt. Hier ist
    das GERÜST + die skill-spezifischen Prinzipien.
    """
    principles = SKILL_PRINCIPLES.get(skill_id, SKILL_PRINCIPLES["sun_mate"])

    return {
        "skill_id": skill_id,
        "framework_version": "1.0.0",
        "mission": mission[:500] + ("..." if len(mission) > 500 else ""),
        "analysis": {
            "phase1_mission_definition": {
                "mission": mission[:200],
                "objective": "Strategiebericht aus " + skill_id + "-Perspektive",
                "constraints": ["domän-agnostisch", "quellenbelegt", "neutral"],
            },
            "phase2_battlefield_mapping": {
                "actors": ["Akteur A", "Akteur B", "Instanz"],
                "resources": ["Ressource 1", "Ressource 2"],
                "terrain": "Kontext-abhängig",
            },
            "phase3_terrain_analysis": {
                "advantages": ["Vorteil 1"],
                "vulnerabilities": ["Schwäche 1"],
                "key_terrain": "Hebelpunkt laut " + skill_id,
            },
            "phase4_intelligence_assessment": {
                "known_facts": ["Fakt aus Problemstellung"],
                "assumptions": ["Annahme 1"],
                "unknowns": ["Offen 1"],
                "missing_intelligence": ["Lücke 1"],
                "confidence_per_conclusion": {"c1": "medium"},
            },
            "phase5_strategic_principles": {
                "principles_applied": principles,
            },
            "phase6_courses_of_action": [
                {"id": "A", "name": "Primäre Strategie",
                 "priority": "primary", "risk": "niedrig",
                 "payoff": "hoch", "time_horizon": "Monate"},
                {"id": "B", "name": "Parallele Strategie",
                 "priority": "parallel", "risk": "niedrig",
                 "payoff": "mittel", "time_horizon": "Monate"},
                {"id": "C", "name": "Fallback",
                 "priority": "ultima ratio", "risk": "hoch",
                 "payoff": "mittel", "time_horizon": "Jahre"},
            ],
            "phase7_counter_strategy": {
                "anticipated": ["Gegenzug der Gegenseite"],
                "mitigation": ["Neutrale Framing"],
            },
            "phase8_optimization": {
                "tempo": "schnell genug, langsam genug",
                "blend": skill_id + " + systems",
            },
            "phase9_final_recommendation": {
                "primary_coa": "A",
                "fallback_coa": "C",
                "confidence": "medium",
            },
            "context_dimensions": {
                "domain": "aus Problemstellung extrahiert",
            },
        },
        "metrics": {
            "initiative_score": 75,
            "terrain_advantage": 65,
            "resource_efficiency": 80,
            "conflict_avoidance": 80,
            "strategic_exposure": 30,
        },
        "sources": [],
        "report": {
            "executive_summary": "Aus " + skill_id + "-Perspektive: empfohlene Strategie A (primär).",
            "recommended_strategy": "COA-A",
            "reasoning": "Dominante Strategie laut " + skill_id + "-Prinzipien.",
            "implementation_steps": ["Schritt 1", "Schritt 2"],
            "decision_points": ["Entscheidung 1"],
            "warning_signs": ["Warnzeichen 1"],
            "fallback_plans": ["Fallback C bei Ablehnung"],
            "strategic_principles_applied": principles,
            "confidence_assessment": {"overall": "medium"},
            "detailed_strategies": [
                {"coa": "A", "narrative": "Primäre Strategie.",
                 "rationale": skill_id + "-Prinzipien"},
            ],
            "future_prediction": {
                "is_object": True,
                "if_we_act": [
                    {"horizon": "3_months",
                     "scenario": "Erste Reaktion der Instanz"},
                    {"horizon": "6_months",
                     "scenario": "Nachfrage bei Stillstand"},
                    {"horizon": "12_months",
                     "scenario": "Zielerreichung oder Korrektur"},
                ],
                "if_we_wait": [
                    {"horizon": "12_months",
                     "scenario": "Verwischung der Spuren"},
                ],
            },
            "gabor_mate_counsel": "Neutraler Lagebericht — keine Personen-Marke.",
        },
        "cross_framework_themes": [
            "Aufsichtsweg primaer, Klageerzwingung nur Fallback",
            "COA-A als primäre Strategie",
        ],
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 analyze.py <problemstellung.txt> <output.json> [--skill ID]")
        sys.exit(1)
    mission_path = pathlib.Path(sys.argv[1])
    out_path = pathlib.Path(sys.argv[2])
    skill_id = "sun_mate"
    if "--skill" in sys.argv:
        skill_id = sys.argv[sys.argv.index("--skill") + 1]

    mission = mission_path.read_text(encoding="utf-8")
    result = analyze(mission, skill_id)
    result["generated_at"] = datetime.date.today().isoformat()
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Analyse ({skill_id}) -> {out_path.name}")
    print(f"  Mission: {len(mission)} Zeichen")
    print(f"  Principles: {len(result['analysis']['phase5_strategic_principles']['principles_applied'])}")


if __name__ == "__main__":
    main()
