# benchmarking/metrics/critic.py
from typing import Dict, Any, Optional, List

from benchmarking.utils import extract_json_from_text

METRIC_KEYS = [
    "agent",
    "json_valid",
    "schema_compliance",
    "score_range_validity",
    "consistency_score",
    "issue_completeness",
    "latency",
    "response_length",
    "agent_score",
]


def is_valid_score_range(value: Any) -> bool:
    """Check if value is a valid score [0-100]."""
    return isinstance(value, (int, float)) and 0 <= value <= 100


def critic_metrics(response_text: str, latency: float, level: str = "beginner") -> Dict[str, Any]:
    """
    Calculate metrics for Critic agent response.
    
    Scoring:
    - schema_compliance (25pts): Has required fields
    - score_range_validity (25pts): Score in [0-100]
    - consistency_score (25pts): Score logically matches approval (level-aware thresholds)
    - issue_completeness (25pts): Both types of issues present
    
    Args:
        response_text: Raw LLM response
        latency: Response latency in seconds
        level: Difficulty level (beginner/intermediate/advanced) for consistency score thresholds
        
    Returns:
        Dict with all metrics
    """
    parsed = extract_json_from_text(response_text)

    metrics = {
        "agent": "critic",
        "json_valid": parsed is not None,
        "schema_compliance": False,
        "score_range_validity": False,
        "consistency_score": 0,
        "issue_completeness": 0,
        "latency": round(latency, 2),
        "response_length": len(response_text),
        "agent_score": 0
    }

    if parsed:
        schema_required = ["score", "approved", "module_issues", "global_issues"]
        schema_ok = all(k in parsed for k in schema_required)
        score_ok = is_valid_score_range(parsed.get("score"))

        module_issues = parsed.get("module_issues", [])
        global_issues = parsed.get("global_issues", [])

        # BUG #3 FIX: Check field presence, not content (empty lists are valid for good courses)
        issues_present = isinstance(module_issues, list) and isinstance(global_issues, list)
        issue_completeness = 100 if issues_present else 0

        approved = bool(parsed.get("approved"))
        numeric_score = parsed.get("score") if isinstance(parsed.get("score"), (int, float)) else 0
        
        # Level-based consistency threshold (FIX #7: Changed threshold from 50 to 70)
        if level.lower() == "advanced":
            consistency_threshold = 80  # Stricter for advanced
        elif level.lower() == "intermediate":
            consistency_threshold = 70  # Standard for intermediate
        else:  # beginner or default
            consistency_threshold = 60  # More tolerant for beginner
        
        consistency_ok = (numeric_score >= consistency_threshold and approved) or (numeric_score < consistency_threshold and not approved)

        # Weighted scoring (100 points)
        score = 0
        score += 25 if schema_ok else 0           # schema_compliance (25%)
        score += 25 if score_ok else 0            # score_range_validity (25%)
        score += 25 if consistency_ok else 0      # consistency_score (25%)
        score += 25 if issue_completeness == 100 else int(issue_completeness * 0.25)  # issue_completeness (25%)

        metrics.update({
            "schema_compliance": schema_ok,
            "score_range_validity": score_ok,
            "consistency_score": 100 if consistency_ok else 0,
            "issue_completeness": issue_completeness,
            "agent_score": min(score, 100)
        })

    return metrics
