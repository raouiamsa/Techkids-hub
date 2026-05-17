# benchmarking/comp2_agents_llm_comparaison.py
"""
COMP2 Multi-Agent LLM Comparison Benchmarking Tool

This tool evaluates 4 agents (Architect, Writer, Enricher, Critic) across
multiple LLM models (phi3, mistral, llama3.1) with comprehensive metrics
including RAGAS evaluation via Groq API.

Usage:
    python comp2_agents_llm_comparaison.py
    python comp2_agents_llm_comparaison.py --models phi3:latest,mistral:latest
    python comp2_agents_llm_comparaison.py --no-ragas
"""

import argparse
import csv
import json
import os
import sys
import time
import statistics
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from dotenv import load_dotenv
# Charger le .env depuis apps/ai-brain (parent de benchmarking)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# psutil memory measurement removed — no runtime dependency here

# Add parent to path for imports
AI_BRAIN_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_BRAIN_DIR))

# Import configuration
from benchmarking.config import Config
from benchmarking.language_detector import detect_language_from_topic
from benchmarking.metrics import architect_metrics, writer_metrics, enricher_metrics, critic_metrics
from benchmarking.metrics.architect import METRIC_KEYS as ARCHITECT_KEYS
from benchmarking.metrics.writer import METRIC_KEYS as WRITER_KEYS
from benchmarking.metrics.enricher import METRIC_KEYS as ENRICHER_KEYS
from benchmarking.metrics.critic import METRIC_KEYS as CRITIC_KEYS
from benchmarking.metrics.llm_score import (
    compute_hallucination_rate,
    compute_llm_score,
    compute_rag_score,
    compute_final_score,
)
from ragas_integration.evaluator import LocalRagasEvaluator
from utils import extract_json_from_text

# Try retriever (optional)
try:
    from strategy_final import get_final_strategy, get_retriever_from_strategy
    RETRIEVAL_AVAILABLE = True
except Exception:
    RETRIEVAL_AVAILABLE = False


# ============================================================
# Logging
# ============================================================

def log(msg: str, level: str = "INFO"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


# ============================================================
# Ollama API (with requests + retries)
# ============================================================

def create_session_with_retries(
    retries: int = 3,
    backoff_factor: float = 0.5,
    timeout: int = 300
) -> requests.Session:
    """Create requests session with automatic retries."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def call_ollama_api(
    model: str,
    prompt: str,
    api_url: str = "http://localhost:11434/api/generate",
    max_tokens: int = 700,
    timeout: int = 600,
    enforce_json: bool = True,
    seed: Optional[int] = None,
    temperature: float = 0.0,
) -> Tuple[Optional[str], float, Optional[float]]:
    """Call Ollama API avec streaming pour mesurer le TTFT.

    Returns:
        (response_text, latency_seconds, ttft_ms)
        ttft_ms = Time-To-First-Token en millisecondes
    """
    start = time.time()
    ttft_ms: Optional[float] = None
    tokens: List[str] = []

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if seed is not None:
        payload["options"]["seed"] = seed
    if enforce_json:
        payload["format"] = "json"

    try:
        session = create_session_with_retries()
        with session.post(api_url, json=payload, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = chunk.get("response", "")
                if token and ttft_ms is None:
                    ttft_ms = round((time.time() - start) * 1000, 1)
                tokens.append(token)
                if chunk.get("done"):
                    break
        latency = time.time() - start
        return "".join(tokens).strip(), latency, ttft_ms

    except Exception as e:
        log(f"Ollama API error: {e}", "ERROR")
        return None, time.time() - start, None


def measure_memory_mb() -> float:
    """Retourne la mémoire RSS du processus courant en MB."""
    # Deprecated. Memory measurement removed from exports and replaced
    # by external monitoring when needed. Keep signature for backward
    # compatibility but return 0.0.
    return 0.0


# ============================================================
# Document Retrieval
# ============================================================

def retrieve_context_documents(retriever, query: str, limit: int = 3) -> List[str]:
    """Retrieve context documents using hybrid search."""
    if not retriever:
        return []

    try:
        docs = retriever.search_hybrid(query=query, limit=limit)
        results = []

        for i, doc in enumerate(docs[:limit], 1):
            title = doc.get("title", "")
            content = doc.get("content", "")
            results.append(f"[Doc {i}] {title}\n{content}")

        return results

    except Exception as e:
        log(f"Retrieval error: {e}", "WARN")
        return []


def log_context_quality(context_docs: List[str], query: str):
    """Log la qualité du contexte récupéré."""
    if not context_docs:
        log(f"  Context: 0 documents retrieved for '{query}'", "WARN")
        return
    
    total_chars = sum(len(doc) for doc in context_docs)
    total_words = sum(len(doc.split()) for doc in context_docs)
    avg_doc_size = total_chars // len(context_docs) if context_docs else 0
    
    log(f"  Context: {len(context_docs)} doc(s), {total_words} words, {total_chars} chars, avg={avg_doc_size}c/doc")
    
    # Show first 100 chars of each doc as preview
    for i, doc in enumerate(context_docs, 1):
        preview = doc[:100].replace("\n", " ")
        log(f"    [Doc {i}] {preview}...")


def format_context_for_prompt(documents: List[str]) -> str:
    """Format retrieved documents for prompt injection."""
    if not documents:
        return ""
    return "\n--- CONTEXTE ---\n" + "\n\n".join(documents) + "\n--- FIN ---\n"


# ============================================================
# Result Building
# ============================================================

def build_result_row(
    topic: str,
    model: str,
    agent: str,
    metrics: Dict[str, Any],
    age: int = 0,
    level: str = "",
    run_index: Optional[int] = None,
    seed: Optional[int] = None,
    repeat_count: Optional[int] = None,
    ragas_runtime_status: str = "n/a"
) -> Dict[str, Any]:
    """Construit une ligne CSV ne contenant QUE les colonnes pertinentes pour l'agent.

    Colonnes communes (tous les agents) :
        topic, model, agent, json_valid, latency,
        ttft_ms, llm_score, agent_score, final_score,
        response_length, details

    Colonnes spécifiques :
        architect → schema_compliance, module_count, module_completeness, pedagogical_structure
        writer    → schema_compliance, word_count, examples_count, readability,
                    content_coverage, tone_*, ragas_*, rag_score
        enricher  → schema_validity, options_validity, answer_index_validity,
                    diversity_score, exercise_count, valid_exercises
        critic    → schema_compliance, score_range_validity, consistency_score, issue_completeness
    """
    # ── Colonnes communes ─────────────────────────────────────────────────────
    row: Dict[str, Any] = {
        "topic":              topic,
        "age":                age,
        "level":              level,
        "model":              model,
        "agent":              agent,
        "run_index":          run_index if run_index is not None else "",
        "seed":               seed if seed is not None else "",
        "repeat_count":       repeat_count if repeat_count is not None else "",
        "json_valid":         metrics.get("json_valid", ""),
        "latency":            metrics.get("latency", 0),
        "ttft_ms":            metrics.get("ttft_ms", ""),
        "llm_score":          metrics.get("llm_score", ""),
        "agent_score":        metrics.get("agent_score", 0),
        "final_score":        metrics.get("final_score", ""),
        "response_length":    metrics.get("response_length", 0),
        "generated_content":  metrics.get("generated_content", ""),
        "details":            json.dumps(metrics),
    }

    if agent in ("architect", "writer"):
        row["context_docs_count"] = metrics.get("context_docs_count", 0)

    if agent == "writer":
        row["hallucination_rate"] = metrics.get("hallucination_rate", "")

    # ── Colonnes spécifiques par agent ────────────────────────────────────────
    if agent == "architect":
        row.update({
            "schema_compliance":    metrics.get("schema_compliance", ""),
            "module_count":         metrics.get("module_count", ""),
            "module_completeness":  metrics.get("module_completeness", ""),
            "pedagogical_structure":metrics.get("pedagogical_structure", ""),
        })

    elif agent == "writer":
        row.update({
            "schema_compliance":        metrics.get("schema_compliance", ""),
            "word_count":               metrics.get("word_count", ""),
            "examples_count":           metrics.get("examples_count", ""),
            "readability":              metrics.get("readability", ""),
            "lix_value":                metrics.get("lix_value", ""),
            "content_coverage":         metrics.get("content_coverage", ""),
            "tone_encouragement":       metrics.get("tone_encouragement", ""),
            "tone_simplicity":          metrics.get("tone_simplicity", ""),
            "tone_engagement":          metrics.get("tone_engagement", ""),
            "tone_source":              metrics.get("tone_source", ""),
            # RAG layer (writer uniquement)
            "ragas_faithfulness":       metrics.get("ragas_faithfulness", ""),
            "ragas_answer_relevancy":   metrics.get("ragas_answer_relevancy", ""),
            "ragas_context_precision":  metrics.get("ragas_context_precision", ""),
            "ragas_context_recall":     metrics.get("ragas_context_recall", ""),
            "ragas_avg":                metrics.get("ragas_avg", ""),
            "ragas_status":             metrics.get("ragas_status", ragas_runtime_status),
            "rag_score":                metrics.get("rag_score", ""),
        })

    elif agent == "enricher":
        row.update({
            "schema_validity":      metrics.get("schema_validity", ""),
            "options_validity":     metrics.get("options_validity", ""),
            "answer_index_validity":metrics.get("answer_index_validity", ""),
            "diversity_score":      metrics.get("diversity_score", ""),
            "exercise_count":       metrics.get("exercise_count", ""),
            "valid_exercises":      metrics.get("valid_exercises", ""),
        })

    elif agent == "critic":
        row.update({
            "schema_compliance":    metrics.get("schema_compliance", ""),
            "score_range_validity": metrics.get("score_range_validity", ""),
            "consistency_score":    metrics.get("consistency_score", ""),
            "issue_completeness":   metrics.get("issue_completeness", ""),
        })

    return row


# ============================================================
# Main Benchmarking
# ============================================================

def run_comp2_comparison(config: Config):
    """Run COMP2 multi-agent comparison across models.
    
    Args:
        config: Configuration object (pre-configured with CLI args if applicable)
    """
    log("=== COMP2 Agents LLM Comparison ===")

    # Initialize retriever
    retriever = None
    if RETRIEVAL_AVAILABLE:
        try:
            strategy = get_final_strategy()
            retriever = get_retriever_from_strategy(strategy)
            log("Retriever initialized")
        except Exception as e:
            log(f"Retriever failed: {e}", "WARN")

    # Initialize RAGAS evaluator
    ragas_evaluator = None
    ragas_runtime_status = "disabled"

    if config.use_ragas:
        try:
            ragas_evaluator = LocalRagasEvaluator(
                model=config.ragas_model,
                cache_dir=config.cache_dir,
                use_cache=config.ragas_cache_enabled
            )
            log(f"RAGAS evaluator initialized (Groq {config.ragas_model})")
            ragas_runtime_status = "enabled"
        except Exception as e:
            log(f"RAGAS init failed: {e}", "WARN")
            ragas_runtime_status = "init_failed"

    # Colonnes par défaut par agent (pour s'assurer qu'elles apparaissent dans le CSV)
    agent_default_keys = {
        "architect": list(ARCHITECT_KEYS),
        "writer":    list(WRITER_KEYS),
        "enricher":  list(ENRICHER_KEYS),
        "critic":    list(CRITIC_KEYS),
    }

    # CSV headers
    headers = [
        # Identification
        "topic", "age", "level", "model", "agent", "run_index", "seed", "repeat_count",
        # Agent metrics
        "json_valid", "schema_compliance", "word_count",
        "examples_count", "readability", "lix_value", "content_coverage",
        "tone_encouragement", "tone_simplicity", "tone_engagement",
        # RAGAS
        "ragas_faithfulness", "ragas_answer_relevancy",
        "ragas_context_precision", "ragas_context_recall",
        "ragas_avg", "ragas_status",
        # LLM-layer
        "hallucination_rate", "ttft_ms", "latency",
        # Composite scores
        "rag_score", "llm_score", "agent_score", "final_score",
        # Debug
        "response_length", "details",
    ]

    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Main comparison loop ──────────────────────────────────────────

    for topic_cfg in config.topics:
        topic = topic_cfg["topic"]
        age = topic_cfg.get("age", 12)
        level = topic_cfg.get("level", "beginner")
        reference_answer = topic_cfg.get("reference_answer", "")
        repeats = int(topic_cfg.get("repeats", 1) or 1)
        seed_base = topic_cfg.get("seed_base")

        # Retrieve context
        context_query = f"{topic} | age={age} | level={level}"
        context_docs = retrieve_context_documents(retriever, context_query, limit=3)
        context_block = format_context_for_prompt(context_docs)
        n_docs = len(context_docs)
        log_context_quality(context_docs, context_query)
        if n_docs > 0:
            log(f"  RAG context: {n_docs} doc(s) retrieved for '{topic}'")
        else:
            log(f"  RAG context: 0 docs found for '{topic}' — hallucination heuristique sera élevée", "WARN")

        for model in config.models:
            for repeat_index in range(repeats):
                run_seed = None if seed_base is None else int(seed_base) + repeat_index
                if repeats > 1:
                    log(f"Testing {topic} with {model} (Repeat {repeat_index + 1}/{repeats}, seed={run_seed if run_seed is not None else 'n/a'})")
                else:
                    log(f"Testing {topic} with {model}")

                writer_content = ""

                # ── Phase 1: Architect + Writer (with RAG context) ──
                detected_language = detect_language_from_topic(topic, model=model)
                phase1_tests = [
                    ("architect", config.load_prompt(
                        "architect",
                        topic=topic,
                        age=topic_cfg["age"],
                        level=topic_cfg["level"],
                        language=detected_language,
                        context=context_block
                    )),
                    ("writer", config.load_prompt(
                        "writer",
                        module_title=f"{topic} Introduction",
                        topic=topic,
                        age=topic_cfg["age"],
                        level=topic_cfg["level"],
                        language=detected_language,
                        index=0,
                        context=context_block,
                        tone_guideline=config.get_tone_guideline(age),
                        feedback="",
                    )),
                ]

                for agent, prompt in phase1_tests:
                    log(f"  > {agent}")

                    max_tok = getattr(config, f"ollama_max_tokens_{agent}", 700)
                    agent_temp = 0.3 if agent == "writer" else 0.0
                    response, latency, ttft_ms = call_ollama_api(
                        model,
                        prompt,
                        api_url=config.ollama_url,
                        max_tokens=max_tok,
                        timeout=config.ollama_timeout,
                        seed=run_seed,
                        temperature=agent_temp
                    )

                    if not response:
                        log(f"    No response from {agent}", "WARN")
                        continue

                    # Capture writer output for downstream agents
                    if agent == "writer":
                        _parsed = extract_json_from_text(response) or {}
                        if isinstance(_parsed, list) and _parsed and isinstance(_parsed[0], dict):
                            _parsed = _parsed[0]
                        writer_content = (
                            _parsed.get("content", "") if isinstance(_parsed, dict) else ""
                        )

                    # Compute agent metrics
                    if agent == "architect":
                        metrics = architect_metrics(response, latency, level=topic_cfg["level"])
                    elif agent == "writer":
                        ragas_scores = None
                        if ragas_evaluator is not None:
                            try:
                                answer_text = writer_content
                                explicit_gt = reference_answer if reference_answer else ""
                                ragas_scores = ragas_evaluator.evaluate_generation(
                                    question=f"Write a {topic_cfg['level']} module about {topic} for age {topic_cfg['age']}",
                                    answer=answer_text,
                                    context="\n\n".join(context_docs),
                                    ground_truth=explicit_gt,
                                    context_docs=context_docs,
                                    topic=topic,
                                )
                            except Exception as e:
                                log(f"    RAGAS eval failed: {e}", "WARN")
                                ragas_runtime_status = "eval_failed"
                        metrics = writer_metrics(response, latency, ragas_scores=ragas_scores, topic=topic, age=topic_cfg["age"], level=topic_cfg["level"], groq_api_key=ragas_evaluator.api_key if ragas_evaluator else None)

                    # ── LLM-layer & composite scores ──
                    ragas_faith = (
                        ragas_scores.get("faithfulness") if (agent == "writer" and ragas_scores) else None
                    )
                    log_context_quality(context_docs, topic)
                    hallucination = compute_hallucination_rate(
                        response, context_docs, ragas_faithfulness=ragas_faith, agent=agent
                    )
                    llm_s = compute_llm_score(
                        json_valid=bool(metrics.get("json_valid")),
                        hallucination_rate=hallucination,
                        latency=latency,
                        ttft_ms=ttft_ms,
                    )
                    rag_s = compute_rag_score(ragas_scores) if agent == "writer" else None
                    final_s = compute_final_score(
                        agent_score=float(metrics.get("agent_score", 0)),
                        llm_score=llm_s,
                        rag_score=rag_s,
                    )
                    metrics.update({
                        "generated_content":   response,
                        "ttft_ms":             ttft_ms,
                        "llm_score":           llm_s,
                        "rag_score":           rag_s,
                        "final_score":         final_s,
                    })

                    if agent == "writer":
                        metrics["hallucination_rate"] = hallucination

                    if agent in ("architect", "writer"):
                        metrics["context_docs_count"] = n_docs

                    # Store result
                    results.append(build_result_row(
                        topic, model, agent, metrics,
                        age=age,
                        level=level,
                        run_index=repeat_index + 1,
                        seed=run_seed,
                        repeat_count=repeats,
                        ragas_runtime_status=ragas_runtime_status if agent == "writer" else "n/a"
                    ))

                    log(f"    agent={metrics['agent_score']} llm={llm_s} rag={rag_s} final={final_s}")

                # ── Phase 2: Enricher + Critic (with writer content) ──
                content_snippet = writer_content[:2000] if writer_content else ""
                if not content_snippet:
                    log("  Writer content empty: enricher/critic without context", "WARN")

                # Le contenu est injecté via les placeholders {module_content} / {course_summary}
                # dans les templates enricher.txt et critic.txt — pas de prepend manuel nécessaire.
                enricher_prompt = config.load_prompt(
                    "enricher",
                    module_content=content_snippet,
                    age=topic_cfg["age"],
                    lang=detected_language
                )
                critic_prompt = config.load_prompt(
                    "critic",
                    course_summary=content_snippet,
                    age=topic_cfg["age"],
                    language=detected_language,
                    topic=topic
                )

                for agent, prompt in [("enricher", enricher_prompt), ("critic", critic_prompt)]:
                    log(f"  > {agent}")

                    response, latency, ttft_ms = call_ollama_api(
                        model,
                        prompt,
                        api_url=config.ollama_url,
                        max_tokens=config.ollama_max_tokens_enricher if agent == "enricher" else config.ollama_max_tokens_critic,
                        timeout=config.ollama_timeout,
                        seed=run_seed
                    )

                    if not response:
                        log(f"    No response from {agent}", "WARN")
                        continue

                    # Compute agent metrics
                    if agent == "enricher":
                        metrics = enricher_metrics(response, latency, level=topic_cfg["level"])
                    else:  # critic
                        metrics = critic_metrics(response, latency, level=topic_cfg["level"])

                    # LLM-layer & composite scores
                    log_context_quality(context_docs, topic)
                    hallucination = compute_hallucination_rate(response, context_docs, agent=agent)
                    llm_s = compute_llm_score(
                        json_valid=bool(metrics.get("json_valid")),
                        hallucination_rate=hallucination,
                        latency=latency,
                        ttft_ms=ttft_ms,
                    )
                    final_s = compute_final_score(
                        agent_score=float(metrics.get("agent_score", 0)),
                        llm_score=llm_s,
                        rag_score=None,
                    )
                    metrics.update({
                        "generated_content": response,
                        "ttft_ms": ttft_ms,
                        "llm_score": llm_s,
                        "rag_score": None,
                        "final_score": final_s,
                    })

                    # hallucination_rate is only exported for writer

                    # Store result
                    results.append(build_result_row(
                        topic, model, agent, metrics,
                        age=age,
                        level=level,
                        run_index=repeat_index + 1,
                        seed=run_seed,
                        repeat_count=repeats
                    ))
                    log(f"    agent={metrics['agent_score']} llm={llm_s} final={final_s}")

    # ── Aggregate results and save ────────────────────────────────

    results_by_topic_agent = defaultdict(list)
    for result in results:
        key = (result["topic"], result["agent"])
        results_by_topic_agent[key].append(result)

    written_paths = []

    for (topic_name, agent), agent_results in sorted(results_by_topic_agent.items()):
        # Extract age and level from first result (same for all rows in group)
        first_result = agent_results[0] if agent_results else {}
        age_val = first_result.get("age", "")
        level_val = first_result.get("level", "")
        
        # BUG #8 FIX: Use session timestamp, not new datetime per agent (for grouping)
        output_path = config.outputs_dir / f"comp2_{topic_name}_age{age_val}_level{level_val}_{agent}_models-{timestamp}.csv"

        # Compute which columns actually contain data for this agent
        # Collect all keys present in result dicts (CSV DictWriter requires fieldnames to include every dict key)
        present_keys = set()
        for row in agent_results:
            present_keys.update(row.keys())

        # Include agent default keys to ensure expected metrics are present
        default_keys = agent_default_keys.get(agent, [])
        present_keys.update(default_keys)

        # Ensure basic/common columns are always present
        mandatory = ["topic", "model", "agent", "score", "details"]
        present_keys.update(mandatory)

        # Preferred ordering: keep original headers order when possible
        ordered_fieldnames = [h for h in headers if h in present_keys]
        # Append any additional keys not in global headers
        extra = [k for k in sorted(present_keys) if k not in ordered_fieldnames]
        ordered_fieldnames.extend(extra)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ordered_fieldnames)
            writer.writeheader()
            writer.writerows(agent_results)

        written_paths.append(output_path)

    # ── Statistical Summary ────────────────────────────────────────

    log("\n=== SUMMARY ===")
    aggregate: Dict[Any, Dict[str, list]] = defaultdict(lambda: {"agent": [], "llm": [], "final": []})

    for result in results:
        key = (result["model"], result["agent"])
        aggregate[key]["agent"].append(result.get("agent_score", 0))
        aggregate[key]["llm"].append(result.get("llm_score", 0) or 0)
        aggregate[key]["final"].append(result.get("final_score", 0) or 0)

    for (model, agent), scores in sorted(aggregate.items()):
        a_mean  = statistics.mean(scores["agent"])
        l_mean  = statistics.mean(scores["llm"])
        f_mean  = statistics.mean(scores["final"])
        log(
            f"{model} | {agent}: "
            f"agent={a_mean:.1f}  llm={l_mean:.1f}  final={f_mean:.1f}"
        )

    for path in written_paths:
        log(f"Saved: {path}")


# ============================================================
# CLI Arguments
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="COMP2 Multi-Agent LLM Comparison Benchmarking Tool"
    )

    parser.add_argument(
        "--models",
        type=str,
        help="Comma-separated list of Ollama models to test"
    )
    parser.add_argument(
        "--no-ragas",
        action="store_true",
        help="Disable RAGAS evaluation even if available"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Run single-topic benchmark (overrides config topics)"
    )
    parser.add_argument(
        "--age",
        type=int,
        help="Age for the single-topic run (used with --topic)"
    )
    parser.add_argument(
        "--level",
        type=str,
        help="Level for the single-topic run (used with --topic)"
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="[DEPRECATED - auto-detected] Language for the single-topic run (used with --topic)"
    )
    parser.add_argument(
        "--reference",
        type=str,
        default=None,
        help="Optional reference_answer text for the single-topic run"
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of times to repeat the benchmark for each model (default: 1)"
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=None,
        help="Base seed for deterministic runs (if set, runs will use seed, seed+1, seed+2, ... for repeats)"
    )

    args = parser.parse_args()

    # Initialize config
    config = Config()

    # Override with CLI args if provided
    if args.models:
        config.models = [m.strip() for m in args.models.split(",")]

    if args.no_ragas:
        config.use_ragas = False

    # If a single topic is provided via CLI, override config.topics for a smoke test
    if args.topic:
        cfg_topic = {
            "topic": args.topic,
            "age": args.age if args.age is not None else (config.topics[0].get("age") if config.topics else 12),
            "level": args.level if args.level is not None else (config.topics[0].get("level") if config.topics else "beginner"),
            "reference_answer": args.reference if args.reference is not None else (config.topics[0].get("reference_answer") if config.topics else ""),
            "repeats": args.repeats,
            "seed_base": args.seed_base,
        }
        config.topics = [cfg_topic]
    else:
        # Apply CLI args to all topics if no single topic is specified
        for topic_cfg in config.topics:
            topic_cfg["repeats"] = args.repeats
            topic_cfg["seed_base"] = args.seed_base

    # Pass config to main function (FIX: was creating new config inside function)
    run_comp2_comparison(config)
