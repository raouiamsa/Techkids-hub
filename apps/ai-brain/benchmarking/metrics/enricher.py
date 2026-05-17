from typing import Dict, Any, Optional, List

from benchmarking.utils import extract_json_from_text

METRIC_KEYS = [
    "agent",
    "json_valid",
    "schema_validity",
    "options_validity",
    "answer_index_validity",
    "diversity_score",
    "exercise_count",
    "valid_exercises",
    "latency",
    "response_length",
    "agent_score",
]


def normalized_question(text: str) -> str:
    """Normalize question text for comparison."""
    import re
    return re.sub(r"\s+", " ", text.strip().lower())


def safe_ratio(part: int, total: int) -> float:
    """Calculate percentage safely."""
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def enricher_metrics(response_text: str, latency: float, level: str = "beginner") -> Dict[str, Any]:
    """
    Calculate metrics for Enricher agent response.
    
    Scoring:
    - schema_validity (20pts): Valid QCM structure
    - options_validity (25pts): 4 options per question
    - answer_index_validity (25pts): Correct index [0-3]
    - diversity_score (20pts): Different questions
    - quantity_gate (10pts): At least 2 exercises (beginner), 3 (intermediate), 4 (advanced)
    
    Args:
        response_text: Raw LLM response
        latency: Response latency in seconds
        level: Difficulty level (beginner/intermediate/advanced) for exercise count targets
        
    Returns:
        Dict with all metrics
    """
    parsed = extract_json_from_text(response_text)

    # Accept common wrapped formats: {"exercises": [...]}, {"questions": [...]}, etc.
    if isinstance(parsed, dict):
        for key in ["exercises", "questions", "items", "qcm"]:
            if isinstance(parsed.get(key), list):
                parsed = parsed[key]
                break

    metrics = {
        "agent": "enricher",
        "json_valid": parsed is not None,
        "schema_validity": 0,
        "options_validity": 0,
        "answer_index_validity": 0,
        "diversity_score": 0,
        "exercise_count": 0,
        "valid_exercises": 0,
        "latency": round(latency, 2),
        "response_length": len(response_text),
        "agent_score": 0
    }

    if isinstance(parsed, list):
        valid = 0
        options_valid = 0
        answer_index_valid = 0
        question_buckets = []

        for item in parsed:
            if (
                isinstance(item, dict)
                and "question" in item
                and "options" in item
                and "correct_index" in item
                and "explanation" in item
            ):
                valid += 1

            if isinstance(item, dict):
                question = item.get("question", "")
                options = item.get("options", [])
                correct_index = item.get("correct_index")

                if isinstance(question, str) and question.strip():
                    question_buckets.append(normalized_question(question))

                if isinstance(options, list) and len(options) == 4 and all(str(opt).strip() for opt in options):
                    options_valid += 1

                if isinstance(correct_index, int) and 0 <= correct_index <= 3:
                    answer_index_valid += 1

        unique_questions = len(set(question_buckets))
        diversity_score = safe_ratio(unique_questions, max(1, len(question_buckets)))
        schema_validity = safe_ratio(valid, max(1, len(parsed)))
        options_validity = safe_ratio(options_valid, max(1, len(parsed)))
        answer_index_validity = safe_ratio(answer_index_valid, max(1, len(parsed)))

        # Level-based minimum exercise count
        if level.lower() == "advanced":
            min_exercises = 4
        elif level.lower() == "intermediate":
            min_exercises = 3
        else:  # beginner or default
            min_exercises = 2

        # Weighted scoring (100 points)
        quantity_gate = 100 if len(parsed) >= min_exercises else 50
        score = round(
            (0.20 * schema_validity)
            + (0.25 * options_validity)
            + (0.25 * answer_index_validity)
            + (0.20 * diversity_score)
            + (0.10 * quantity_gate),
            2,
        )

        metrics.update({
            "schema_validity": schema_validity,
            "options_validity": options_validity,
            "answer_index_validity": answer_index_validity,
            "diversity_score": diversity_score,
            "exercise_count": len(parsed),
            "valid_exercises": valid,
            "agent_score": min(int(score), 100)
        })

    return metrics
