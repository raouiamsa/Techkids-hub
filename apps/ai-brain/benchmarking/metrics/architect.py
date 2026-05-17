from typing import Dict, Any, Optional, List

from benchmarking.utils import extract_json_from_text

METRIC_KEYS = [
    "agent",
    "json_valid",
    "schema_compliance",
    "module_count",
    "module_completeness",
    "pedagogical_structure",
    "latency",
    "response_length",
    "agent_score",
]


def safe_ratio(part: int, total: int) -> float:
    """Calculate percentage safely."""
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def architect_metrics(response_text: str, latency: float, level: str = "beginner") -> Dict[str, Any]:
    """
    Calculate metrics for Architect agent response.
    
    Scoring: 
    - json_valid (20pts): Can parse as JSON
    - schema_compliance (30pts): Has required fields
    - module_count (20pts): At least 2 modules
    - module_completeness (20pts): All modules have required subfields
    - pedagogical_structure (10pts): Has objectives + proper ordering
    
    Args:
        response_text: Raw LLM response
        latency: Response latency in seconds
        
    Returns:
        Dict with all metrics
    """
    parsed = extract_json_from_text(response_text)

    # BUG #2 FIX: Include all required fields from architect prompt
    schema_required = ["courseTitle", "modules", "level", "programmingLanguage", "totalDuration", "objectives"]

    metrics = {
        "agent": "architect",
        "json_valid": parsed is not None,
        "schema_compliance": False,
        "module_count": 0,
        "module_completeness": 0,
        "pedagogical_structure": 0,
        "latency": round(latency, 2),
        "response_length": len(response_text),
        "agent_score": 0
    }

    if parsed:
        # Some models return a top-level array with one object.
        if isinstance(parsed, list):
            if parsed and isinstance(parsed[0], dict):
                parsed = parsed[0]
            else:
                parsed = {}

        # Some models wrap expected payload in an envelope object.
        if isinstance(parsed, dict):
            for envelope_key in ["syllabus", "course", "data"]:
                if isinstance(parsed.get(envelope_key), dict):
                    parsed = parsed[envelope_key]
                    break

            # Normalize common alias keys to canonical schema.
            if "courseTitle" not in parsed and isinstance(parsed.get("title"), str):
                parsed["courseTitle"] = parsed["title"]
            if "programmingLanguage" not in parsed and isinstance(parsed.get("language"), str):
                parsed["programmingLanguage"] = parsed["language"]
            if "totalDuration" not in parsed and isinstance(parsed.get("duration"), str):
                parsed["totalDuration"] = parsed["duration"]
            if "objectives" not in parsed and isinstance(parsed.get("learning_objectives"), list):
                parsed["objectives"] = parsed["learning_objectives"]

        # Schema check
        schema_ok = all(k in parsed for k in schema_required)
        modules = parsed.get("modules", [])
        objectives = parsed.get("objectives", [])

        # Module validation
        valid_modules = 0
        progressive_orders = []

        for module in modules if isinstance(modules, list) else []:
            if not isinstance(module, dict):
                continue

            # Module is valid if it has required fields
            has_subtopics = bool(module.get("subTopics") or module.get("subtopics"))
            if all(module.get(field) for field in ["title", "description"]) and has_subtopics:
                valid_modules += 1

            order = module.get("order")
            if isinstance(order, int):
                progressive_orders.append(order)

        module_count = len(modules) if isinstance(modules, list) else 0
        module_completeness = safe_ratio(valid_modules, max(1, module_count))
        progression_ok = bool(progressive_orders) and progressive_orders == sorted(progressive_orders)
        pedagogical_structure = 100 if (bool(objectives) and progression_ok) else 0

        # ── Scoring pondéré (100 points) ───────────────────────────────────
        # json_valid est stocké comme bool mais NON scoré ici.
        # Il est mesuré dans la couche LLM (compute_llm_score → format_score).
        # La cascade naturelle s'applique : si JSON invalide → parsed=None
        # → tous les scores ci-dessous = 0 → agent_score = 0.
        #
        # schema_compliance  (35%) : champs requis présents
        # module_count       (25%) : adapté par level (beginner: 2+, intermediate: 3+, advanced: 4+)
        # module_completeness(25%) : modules complets (titre + description + subtopics)
        # pedagogical_structure(15%): objectifs + progression ordonnée
        
        # Level-based minimum module count
        if level.lower() == "advanced":
            min_modules = 4
        elif level.lower() == "intermediate":
            min_modules = 3
        else:  # beginner or default
            min_modules = 2
        
        score = 0
        score += 35 if schema_ok else 0
        score += 25 if module_count >= min_modules else 0
        score += 25 if module_completeness == 100 else int(module_completeness * 0.25)
        score += 15 if pedagogical_structure == 100 else 0

        metrics.update({
            "schema_compliance": schema_ok,
            "module_count": module_count,
            "module_completeness": module_completeness,
            "pedagogical_structure": pedagogical_structure,
            "agent_score": min(score, 100)
        })

    return metrics
