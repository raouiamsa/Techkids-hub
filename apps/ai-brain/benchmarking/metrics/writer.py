# benchmarking/metrics/writer.py
"""Metrics for Writer agent.

Scoring rationale:
- json_valid (20%): Basic requirement for JSON compliance
- schema_compliance (20%): Has required fields (title, content, word_count)
- word_count (15%): Minimum 1000 words for depth
- readability (15%): LIX readability (age-adapted target)
- examples_count (10%): Code blocks and example mentions
- content_coverage (10%): Educational keywords + topic concept coverage
- tone_simplicity (5%): Language simplicity (informational only)
- RAGAS metrics (5%): Faithfulness, answer_relevancy, context metrics

Total weight: 100%
Note: tone_encouragement moved to Virtual Lab (where feedback is interactive)
"""

import re
import math
from typing import Dict, Any, Optional, List

from benchmarking.utils import extract_json_from_text
from benchmarking.metrics.tone_judge import judge_tone

METRIC_KEYS = [
    "agent",
    "json_valid",
    "schema_compliance",
    "word_count",
    "examples_count",
    "readability",
    "lix_value",
    "educational_richness",
    "keyword_coverage",
    "tone_simplicity",
    "tone_engagement",
    "tone_source",
    "ragas_faithfulness",
    "ragas_answer_relevancy",
    "ragas_context_precision",
    "ragas_context_recall",
    "ragas_avg",
    "ragas_status",
    "latency",
    "response_length",
    "agent_score",
]


def ensure_string(value) -> str:
    """Convert any value to string, handling lists, dicts, etc."""
    if isinstance(value, str):
        return value
    elif isinstance(value, list):
        return " ".join(str(v) for v in value if v)
    elif value is None:
        return ""
    else:
        return str(value)


def count_words(text) -> int:
    """Count words in text."""
    text = ensure_string(text)
    return len(text.split())


def readability_score(text, age: int = 12, level: str = "beginner") -> float:
    """Compute readability using LIX and return an age+level-adapted 0-100 score.

    LIX formula (lower is easier):
      LIX = (words / sentences) + (long_words * 100 / words)
    where long_words = words with length > 6.

    Age + Level targets (expected max LIX):
    - beginner:    age-based -5 (stricter)
    - intermediate: age-based (neutral)
    - advanced:    age-based +5 (more tolerant)

    Base targets by age:
    - age <= 10 : 30
    - age 11-12 : 35
    - age 13-15 : 40
    - age >= 16 : 45

    Scoring:
    - If LIX <= target: score = 100
    - If LIX > target: linear penalty (2.5 points per LIX point above target)
    """
    lix = compute_lix_value(text)
    if lix is None:
        return 0.0

    # Age-based base target
    if age <= 10:
        base_lix = 30.0
    elif age <= 12:
        base_lix = 35.0
    elif age <= 15:
        base_lix = 40.0
    else:
        base_lix = 45.0

    # Level adjustment
    if level.lower() == "beginner":
        target_lix = base_lix - 5.0
    elif level.lower() == "advanced":
        target_lix = base_lix + 5.0
    else:  # intermediate or unknown
        target_lix = base_lix

    if lix <= target_lix:
        score = 100.0
    else:
        score = max(0.0, 100.0 - ((lix - target_lix) * 2.5))

    return round(score, 2)


def compute_lix_value(text) -> Optional[float]:
    """Compute raw LIX value (lower is easier). Returns None if text is empty."""
    text = ensure_string(text)
    words = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    word_count = len(words)
    if word_count == 0:
        return None

    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    long_words = sum(1 for w in words if len(w) > 6)
    lix = (word_count / sentences) + ((long_words * 100.0) / word_count)
    return round(lix, 2)


def content_coverage(text, topic_keywords: List[str]) -> float:
    """Métrique fusionnée : keywords pédagogiques génériques + keywords du topic.

    Remplace educational_richness + keyword_coverage (redondants).
    Score = moyenne pondérée des deux dimensions.
      - Richesse pédagogique (60%) : présence de verbes d'action pédagogiques
      - Couverture du topic (40%)  : présence des concepts clés du sujet
    """
    text_lower = ensure_string(text).lower()

    # Keywords pédagogiques génériques (bilingue FR/EN)
    # Note: exercise, quiz, practice are Enricher responsibility
    pedagogical_kws = [
        "example", "explanation", "understand", "concept", "learn", "tip",
        "code", "snippet", "pattern", "step",
        "exemple", "explication", "comprendre", "concept", "apprendre", "code",
        "découvrir", "étape", "motif",
    ]
    richness_hits = sum(1 for kw in pedagogical_kws if kw in text_lower)
    richness_score = min(100.0, (richness_hits / len(pedagogical_kws)) * 100.0 * 2)

    # Couverture du topic
    topic_hits = sum(1 for kw in topic_keywords if kw.lower() in text_lower)
    topic_score = round((topic_hits / len(topic_keywords)) * 100.0, 2) if topic_keywords else 0.0

    # Moyenne pondérée
    return round(richness_score * 0.6 + topic_score * 0.4, 2)


def educational_richness(text) -> float:
    """Return the pedagogical richness score (0-100)."""
    text_lower = ensure_string(text).lower()
    pedagogical_kws = [
        "example", "explanation", "understand", "concept", "learn", "tip",
        "code", "snippet", "pattern", "step",
        "exemple", "explication", "comprendre", "concept", "apprendre", "code",
        "découvrir", "étape", "motif",
    ]
    richness_hits = sum(1 for kw in pedagogical_kws if kw in text_lower)
    richness_score = min(100.0, (richness_hits / len(pedagogical_kws)) * 100.0 * 2)
    return round(richness_score, 2)


def keyword_coverage(text, topic_keywords: List[str]) -> float:
    """Return the topic keyword coverage score (0-100)."""
    text_lower = ensure_string(text).lower()
    topic_hits = sum(1 for kw in topic_keywords if kw.lower() in text_lower)
    return round((topic_hits / len(topic_keywords)) * 100.0, 2) if topic_keywords else 0.0


def count_examples(text) -> int:
    """Count code blocks and example mentions."""
    text = ensure_string(text)
    if not text:
        return 0

    # BUG #6 FIX: Code fences appear twice (opening + closing), so divide by 2
    code_fences = len(re.findall(r"```", text)) // 2
    example_mentions = len(re.findall(r"\bexample\b", text, re.IGNORECASE)) + len(re.findall(r"\bexemple\b", text, re.IGNORECASE))
    return code_fences + example_mentions



def tone_simplicity_score(text) -> float:
    """Mesure la simplicité du langage (mots courts = score élevé).
    Heuristique statique locale (informative uniquement, non scorée).
    """
    text = ensure_string(text)
    words = text.split()
    if not words:
        return 0.0

    avg_word_length = sum(len(w) for w in words) / len(words)
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_sentence_length = len(words) / sentences

    complexity = (avg_word_length * 10.0) + (avg_sentence_length * 2.0)
    simplicity = max(0.0, 100.0 - complexity)
    return round(simplicity, 2)



def get_dynamic_keywords(topic: str) -> List[str]:
    """Generate keywords dynamically from topic name.
    
    FIX #4: Don't hardcode ["python", "variable", "print", "code"]
    Instead extract from the topic itself.
    
    Example: "Python Variables" → ["python", "variables"]
    """
    # Extract meaningful words from topic (remove common words)
    stopwords = {"for", "to", "of", "the", "a", "an", "in", "on", "at"}
    words = [w.lower() for w in topic.split() if w.lower() not in stopwords and len(w) > 2]
    # Remove duplicates but keep order
    return list(dict.fromkeys(words)) if words else ["code", "learn", "practice"]


def writer_metrics(
    response_text: str,
    latency: float,
    ragas_scores: Optional[Dict[str, Any]] = None,
    topic: str = "",
    age: int = 12,
    level: str = "beginner",
    groq_api_key: Optional[str] = None,  # Kept for backward compatibility, not used
) -> Dict[str, Any]:
    """
    Calculate metrics for Writer agent response.

    Scoring (100 points total):
    - json_valid (20pts): Can parse as JSON
    - schema_compliance (20pts): Has required fields
    - word_count (15pts): At least 1000 words
    - readability (15pts): LIX readability (age+level-adapted)
    - examples_count (10pts): Code blocks + example mentions
    - content_coverage (20pts): Educational keywords + topic concepts
    - RAGAS (5pts): Quality metrics from Groq (if enabled)

    Args:
        response_text : Raw LLM response
        latency       : Response latency in seconds
        ragas_scores  : Optional RAGAS evaluation scores dict
        topic         : Topic name for dynamic keyword extraction
        age           : Target age for readability scoring
        level         : Difficulty level (beginner/intermediate/advanced) for scoring adaptation
        groq_api_key  : Deprecated (tone_encouragement moved to Virtual Lab)

    Returns:
        Dict with all metrics
    """
    parsed = extract_json_from_text(response_text)

    metrics = {
        "agent": "writer",
        "json_valid": parsed is not None,
        "schema_compliance": False,
        "word_count": 0,
        "examples_count": 0,
        "readability": 0,
        "lix_value": "",
        "educational_richness": 0,
        "keyword_coverage": 0,
        "tone_simplicity": 0,
        "ragas_faithfulness": "",
        "ragas_answer_relevancy": "",
        "ragas_context_precision": "",
        "ragas_context_recall": "",
        "ragas_avg": "",
        "ragas_status": "not_computed",
        "latency": round(latency, 2),
        "response_length": len(response_text),
        "agent_score": 0
    }

    if parsed:
        schema_required = ["title", "content", "word_count"]
        
        # Handle both dict and list responses
        if isinstance(parsed, list):
            if parsed and isinstance(parsed[0], dict):
                parsed = parsed[0]
            else:
                parsed = {}
        
        content = ensure_string(parsed.get("content", "") if isinstance(parsed, dict) else "")

        wc = count_words(content)
        # compute separate metrics for richness and keyword coverage
        dynamic_kws = get_dynamic_keywords(topic) if topic else ["code", "learn", "practice"]
        richness = educational_richness(content)
        kw_cov = keyword_coverage(content, dynamic_kws)
        cov = round(richness * 0.6 + kw_cov * 0.4, 2)
        examples_count = count_examples(content)

        # tone_simplicity : INFORMATIVE uniquement (non scorée)
        tone_sim = tone_simplicity_score(content)

        # tone_encouragement + tone_engagement : LLM-as-judge Groq (scorés à 10%)
        tone_enc, tone_eng, tone_source = 0.0, 0.0, "not_computed"
        if content:
            _tone = judge_tone(content, age=age, api_key=groq_api_key)
            tone_enc    = round(_tone.get("encouragement", 0.0), 2)
            tone_eng    = round(_tone.get("engagement",    0.0), 2)
            tone_source = _tone.get("source", "unknown")

        # readability (LIX, age+level-adapted) — scorée à 20%
        readability = readability_score(content, age=age, level=level)
        lix_value = compute_lix_value(content)
        word_count_field = parsed.get("word_count") if isinstance(parsed, dict) else None
        word_count_ok = isinstance(word_count_field, int) or (
            isinstance(word_count_field, str) and word_count_field.strip().isdigit()
        )

        schema_ok = (
            isinstance(parsed, dict)
            and all(k in parsed for k in schema_required)
            and word_count_ok
        )

        # ── Scoring pondéré (100 points) ───────────────────────────────────
        # json_valid : stocké mais NON scoré → mesuré dans LLM layer (format_score).
        # Si JSON invalide → parsed=None → content="" → tous scores = 0 (cascade).
        #
        # schema_compliance  (25%) : champs requis (order, title, content, word_count)
        # word_count         (20%) : ≥ 1000 mots
        # examples_count     (10%) : blocs de code + mentions d'exemples
        # readability        (20%) : LIX (longueur phrases + proportion mots longs)
        # content_coverage   (15%) : richesse pédagogique + couverture du topic
        # tone_llm           (10%) : engagement (Groq judge)
        score = 0
        target_wc = 1000
        score += 25 if schema_ok else 0
        score += 20 if wc >= target_wc else int((wc / target_wc) * 20)
        score += 10 if examples_count > 0 else 0
        score += int(readability * 0.20)
        score += int(cov * 0.15)
        score += int(tone_eng * 0.10)

        metrics.update({
            "schema_compliance":  schema_ok,
            "word_count":         wc,
            "examples_count":     examples_count,
            "readability":        readability,
            "lix_value":          lix_value if lix_value is not None else "",
            "educational_richness": richness,
            "keyword_coverage":   kw_cov,
            "content_coverage":   cov,            # richness*0.6 + kw_cov*0.4
            "tone_simplicity":    tone_sim,       # informatif uniquement (non scoré)
            "tone_engagement":    tone_eng,       # Groq LLM judge
            "tone_source":        tone_source,    # "groq" / "cache" / "static_fallback"
            "agent_score":        min(score, 100),
        })

        # RAGAS scoring (if available)
        if ragas_scores:
            # Filter out non-numeric values (e.g., "n/a") before averaging
            raw_values = [
                ragas_scores.get("faithfulness"),
                ragas_scores.get("answer_relevancy"),
                ragas_scores.get("context_precision"),
                ragas_scores.get("context_recall"),
            ]
            ragas_values = [
                float(v) for v in raw_values
                if isinstance(v, (int, float)) and math.isfinite(float(v))
            ]
            ragas_avg = round(sum(ragas_values) / len(ragas_values), 4) if ragas_values else 0

            metrics.update({
                "ragas_faithfulness": ragas_scores.get("faithfulness", "n/a") if isinstance(ragas_scores.get("faithfulness"), (int, float)) and math.isfinite(float(ragas_scores.get("faithfulness"))) else "n/a",
                "ragas_answer_relevancy": ragas_scores.get("answer_relevancy", "n/a") if isinstance(ragas_scores.get("answer_relevancy"), (int, float)) and math.isfinite(float(ragas_scores.get("answer_relevancy"))) else "n/a",
                "ragas_context_precision": ragas_scores.get("context_precision", "n/a") if isinstance(ragas_scores.get("context_precision"), (int, float)) and math.isfinite(float(ragas_scores.get("context_precision"))) else "n/a",
                "ragas_context_recall": ragas_scores.get("context_recall", "n/a") if isinstance(ragas_scores.get("context_recall"), (int, float)) and math.isfinite(float(ragas_scores.get("context_recall"))) else "n/a",
                "ragas_avg": ragas_avg,
                "ragas_status": "ok",

            })

    return metrics
