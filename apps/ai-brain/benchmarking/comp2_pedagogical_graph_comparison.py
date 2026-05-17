"""COMP2 comparison benchmark using a COMP3 pedagogical graph as context.

This script keeps the COMP2 agent pipeline (architect, writer, enricher, critic)
but replaces the raw RAG context with a pedagogical graph exported by COMP3.

Use this to measure whether a better learning structure improves COMP2 metrics.
"""

import argparse
import csv
import json
import math
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


AI_BRAIN_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_BRAIN_DIR))

env_path = AI_BRAIN_DIR / ".env"
load_dotenv(dotenv_path=env_path)

from benchmarking.config import Config
from benchmarking.language_detector import detect_language_from_topic
from benchmarking.metrics.architect import METRIC_KEYS as ARCHITECT_KEYS
from benchmarking.metrics.writer import METRIC_KEYS as WRITER_KEYS
from benchmarking.metrics.enricher import METRIC_KEYS as ENRICHER_KEYS
from benchmarking.metrics.critic import METRIC_KEYS as CRITIC_KEYS
from benchmarking.metrics.architect import architect_metrics
from benchmarking.metrics.writer import writer_metrics
from benchmarking.metrics.enricher import enricher_metrics
from benchmarking.metrics.critic import critic_metrics
from benchmarking.metrics.llm_score import (
    compute_final_score,
    compute_hallucination_rate,
    compute_llm_score,
    compute_rag_score,
)
from ragas_integration.evaluator import LocalRagasEvaluator
from utils import extract_json_from_text

# Try retriever (optional)
try:
    from benchmarking.strategy_final import get_final_strategy, get_retriever_from_strategy
    RETRIEVAL_AVAILABLE = True
except Exception:
    RETRIEVAL_AVAILABLE = False


def log(msg: str, level: str = "INFO") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def create_session_with_retries(
    retries: int = 3,
    backoff_factor: float = 0.5,
) -> requests.Session:
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
        return "".join(tokens).strip(), time.time() - start, ttft_ms
    except Exception as exc:
        log(f"Ollama API error: {exc}", "ERROR")
        return None, time.time() - start, None


def format_context_for_prompt(documents: List[str]) -> str:
    if not documents:
        return ""
    return "\n--- CONTEXTE ---\n" + "\n\n".join(documents) + "\n--- FIN ---\n"


def latest_graph_export(graph_dir: Path, topic: str, age: int) -> Optional[Path]:
    candidates = sorted(
        graph_dir.glob(f"graph_*_age{age}_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None

    normalized_topic = topic.lower().replace(" ", "")
    for path in candidates:
        if normalized_topic in path.name.lower().replace(" ", ""):
            return path
    return candidates[0]


def build_pedagogical_context_documents(
    graph_file: Path,
    module_id: Optional[str] = None,
    module_name: Optional[str] = None,
    module_index: Optional[int] = None,
    retriever: Any = None,
) -> List[str]:
    try:
        graph_data = json.loads(graph_file.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"Pedagogical graph load error: {exc}", "WARN")
        return []

    modules = graph_data.get("modules", {}) or {}
    concepts = graph_data.get("concepts", {}) or {}
    objectives = graph_data.get("objectives", {}) or {}
    exercises = graph_data.get("exercises", {}) or {}
    relationships = graph_data.get("relationships", {}) or {}

    ordered_modules = sorted(
        modules.values(),
        key=lambda item: (item.get("order_in_curriculum", 0), item.get("id", ""))
    )

    selected_modules = ordered_modules
    if module_id:
        selected_modules = [module for module in ordered_modules if module.get("id") == module_id]
    elif module_name:
        normalized_name = module_name.strip().lower()
        selected_modules = [
            module for module in ordered_modules
            if str(module.get("name", "")).strip().lower() == normalized_name
            or str(module.get("title", "")).strip().lower() == normalized_name
        ]
    elif module_index is not None and ordered_modules:
        safe_index = max(0, min(module_index, len(ordered_modules) - 1))
        selected_modules = [ordered_modules[safe_index]]

    docs: List[str] = [
        "\n".join([
            "[Pedagogical Graph Context]",
            f"topic={graph_data.get('topic', '')}",
            f"age={graph_data.get('age', '')}",
            f"level={graph_data.get('level', '')}",
            f"language={graph_data.get('language', '')}",
            f"selected_modules={len(selected_modules)}",
        ])
    ]

    if module_id and not selected_modules:
        log(f"Module id not found in graph: {module_id}", "WARN")
        return []
    if module_name and not selected_modules:
        log(f"Module name not found in graph: {module_name}", "WARN")
        return []

    for module in selected_modules:
        module_id = module.get("id", "")
        module_name = module.get("name", "Unnamed Module")
        concept_ids = module.get("concepts", []) or []
        objective_ids = module.get("learning_objectives", []) or []
        exercise_ids = module.get("exercises", []) or []

        concept_lines = []
        for concept_id in concept_ids:
            concept = concepts.get(concept_id, {})
            concept_name_val = concept.get('name', concept_id)
            concept_lines.append(
                f"- Concept: {concept_name_val}\n  Définition: {concept.get('definition', '')}\n  Prérequis: {concept.get('prerequisites', [])}"
            )
            if retriever:
                try:
                    chunks = retriever.search_hybrid(query=concept_name_val, limit=2)
                    for i, chunk in enumerate(chunks, 1):
                        content = chunk.get("content", "").replace('\n', ' ').strip()
                        if content:
                            concept_lines.append(f"  [Source Scientifique {i}]: {content}")
                except Exception as e:
                    log(f"Retrieval error for concept {concept_name_val}: {e}", "WARN")

        objective_lines = []
        for objective_id in objective_ids:
            objective = objectives.get(objective_id, {})
            objective_lines.append(
                f"- [{objective.get('type', 'understand')}] {objective.get('description', objective_id)} | concepts={objective.get('associated_concepts', [])}"
            )

        exercise_lines = []
        for exercise_id in exercise_ids:
            exercise = exercises.get(exercise_id, {})
            exercise_lines.append(
                f"- Exercice [{exercise.get('type', 'qcm')}]: {exercise.get('question', exercise_id)}\n  Options: {exercise.get('options', [])}\n  Réponse attendue: {exercise.get('correct_answer', '')}\n  Teste le concept: {exercise.get('tests_concept')}"
            )

        docs.append(
            "\n".join([
                f"[Module {module.get('order_in_curriculum', 0)}] {module_name}",
                f"module_id={module_id}",
                f"prerequisites_modules={module.get('prerequisites_modules', [])}",
                "Concepts:",
                *(concept_lines if concept_lines else ["- none"]),
                "Objectives:",
                *(objective_lines if objective_lines else ["- none"]),
                "Exercises:",
                *(exercise_lines if exercise_lines else ["- none"]),
            ])
        )

    concept_prereqs = relationships.get("concept_prerequisites", {}) or {}
    if concept_prereqs:
        docs.append(
            "[Concept Prerequisites]\n" + "\n".join(
                f"- {cid}: {prereqs}" for cid, prereqs in concept_prereqs.items()
            )
        )

    return docs

def get_selected_pedagogical_module_title(
    graph_file: Path,
    module_id: Optional[str] = None,
    module_name: Optional[str] = None,
    module_index: Optional[int] = None,
) -> Optional[str]:
    try:
        graph_data = json.loads(graph_file.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"Pedagogical graph load error: {exc}", "WARN")
        return None

    modules = graph_data.get("modules", {}) or {}
    ordered_modules = sorted(
        modules.values(),
        key=lambda item: (item.get("order_in_curriculum", 0), item.get("id", ""))
    )

    selected_modules = ordered_modules
    if module_id:
        selected_modules = [module for module in ordered_modules if module.get("id") == module_id]
    elif module_name:
        normalized_name = module_name.strip().lower()
        selected_modules = [
            module for module in ordered_modules
            if str(module.get("name", "")).strip().lower() == normalized_name
            or str(module.get("title", "")).strip().lower() == normalized_name
        ]
    elif module_index is not None and ordered_modules:
        safe_index = max(0, min(module_index, len(ordered_modules) - 1))
        selected_modules = [ordered_modules[safe_index]]

    if not selected_modules:
        return None

    selected_module = selected_modules[0]
    return str(selected_module.get("name") or selected_module.get("title") or "").strip() or None


def list_pedagogical_modules(graph_file: Path) -> List[Dict[str, Any]]:
    try:
        graph_data = json.loads(graph_file.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"Pedagogical graph load error: {exc}", "WARN")
        return []

    modules = graph_data.get("modules", {}) or {}
    ordered_modules = sorted(
        modules.values(),
        key=lambda item: (item.get("order_in_curriculum", 0), item.get("id", ""))
    )

    return [
        {
            "order": module.get("order_in_curriculum", 0),
            "id": module.get("id", ""),
            "name": module.get("name", module.get("title", "Unnamed Module")),
            "title": module.get("title", module.get("name", "Unnamed Module")),
            "concept_count": len(module.get("concepts", []) or []),
            "objective_count": len(module.get("learning_objectives", []) or []),
            "exercise_count": len(module.get("exercises", []) or []),
        }
        for module in ordered_modules
    ]


def build_result_row(
    topic: str,
    model: str,
    agent: str,
    metrics: Dict[str, Any],
    age: int = 0,
    level: str = "",
    ragas_runtime_status: str = "n/a",
    pedagogical_graph_json: str = "",
    run_index: Optional[int] = None,
    seed: Optional[int] = None,
    repeat_count: Optional[int] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "topic": topic,
        "age": age,
        "level": level,
        "model": model,
        "agent": agent,
        "run_index": run_index if run_index is not None else "",
        "seed": seed if seed is not None else "",
        "repeat_count": repeat_count if repeat_count is not None else "",
        "json_valid": metrics.get("json_valid", ""),
        "latency": metrics.get("latency", 0),
        "ttft_ms": metrics.get("ttft_ms", ""),
        "llm_score": metrics.get("llm_score", ""),
        "agent_score": metrics.get("agent_score", 0),
        "final_score": metrics.get("final_score", ""),
        "response_length": metrics.get("response_length", 0),
        "generated_content": metrics.get("generated_content", ""),
        "details": json.dumps(metrics),
        "pedagogical_graph_json": pedagogical_graph_json,
    }

    if agent == "writer":
        row["hallucination_rate"] = metrics.get("hallucination_rate", "")

    if agent == "architect":
        row.update({
            "schema_compliance": metrics.get("schema_compliance", ""),
            "module_count": metrics.get("module_count", ""),
            "module_completeness": metrics.get("module_completeness", ""),
            "pedagogical_structure": metrics.get("pedagogical_structure", ""),
        })
    elif agent == "writer":
        row.update({
            "schema_compliance": metrics.get("schema_compliance", ""),
            "word_count": metrics.get("word_count", ""),
            "examples_count": metrics.get("examples_count", ""),
            "readability": metrics.get("readability", ""),
            "lix_value": metrics.get("lix_value", ""),
            "content_coverage": metrics.get("content_coverage", ""),
            "tone_encouragement": metrics.get("tone_encouragement", ""),
            "tone_simplicity": metrics.get("tone_simplicity", ""),
            "tone_engagement": metrics.get("tone_engagement", ""),
            "tone_source": metrics.get("tone_source", ""),
            "ragas_faithfulness": metrics.get("ragas_faithfulness", ""),
            "ragas_answer_relevancy": metrics.get("ragas_answer_relevancy", ""),
            "ragas_context_precision": metrics.get("ragas_context_precision", ""),
            "ragas_context_recall": metrics.get("ragas_context_recall", ""),
            "ragas_avg": metrics.get("ragas_avg", ""),
            "ragas_status": metrics.get("ragas_status", ragas_runtime_status),
            "rag_score": metrics.get("rag_score", ""),
        })
    elif agent == "enricher":
        row.update({
            "schema_validity": metrics.get("schema_validity", ""),
            "options_validity": metrics.get("options_validity", ""),
            "answer_index_validity": metrics.get("answer_index_validity", ""),
            "diversity_score": metrics.get("diversity_score", ""),
            "exercise_count": metrics.get("exercise_count", ""),
            "valid_exercises": metrics.get("valid_exercises", ""),
        })
    elif agent == "critic":
        row.update({
            "schema_compliance": metrics.get("schema_compliance", ""),
            "score_range_validity": metrics.get("score_range_validity", ""),
            "consistency_score": metrics.get("consistency_score", ""),
            "issue_completeness": metrics.get("issue_completeness", ""),
        })

    return row


def summarize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("topic", "")),
            str(row.get("model", "")),
            str(row.get("agent", "")),
            str(row.get("pedagogical_graph_json", "")),
        )
        grouped[key].append(row)

    summary_rows: List[Dict[str, Any]] = []
    for group_rows in grouped.values():
        base_row = dict(group_rows[0])
        base_row["run_index"] = "avg"
        base_row["seed"] = ""
        base_row["repeat_count"] = len(group_rows)
        base_row["details"] = json.dumps({
            "repeats": len(group_rows),
            "run_indexes": [row.get("run_index", "") for row in group_rows],
        }, ensure_ascii=False)

        numeric_keys = set()
        for row in group_rows:
            for key, value in row.items():
                if isinstance(value, bool) or isinstance(value, (int, float)):
                    numeric_keys.add(key)

        for key in numeric_keys:
            values: List[float] = []
            for row in group_rows:
                value = row.get(key)
                if isinstance(value, bool):
                    values.append(1.0 if value else 0.0)
                elif isinstance(value, (int, float)) and math.isfinite(float(value)):
                    values.append(float(value))
            if values:
                base_row[key] = round(statistics.mean(values), 2)

        summary_rows.append(base_row)

    return summary_rows


def run_pedagogical_comp2(
    config: Config,
    pedagogical_graph_json: Optional[str] = None,
    use_hybrid_rag: bool = False,
) -> List[Dict[str, Any]]:
    log("=== COMP2 Pedagogical Graph Comparison ===")

    ragas_evaluator = None
    ragas_runtime_status = "disabled"
    if config.use_ragas:
        try:
            ragas_evaluator = LocalRagasEvaluator(
                model=config.ragas_model,
                cache_dir=config.cache_dir,
                use_cache=config.ragas_cache_enabled,
            )
            log(f"RAGAS evaluator initialized (Groq {config.ragas_model})")
            ragas_runtime_status = "enabled"
        except Exception as exc:
            log(f"RAGAS init failed: {exc}", "WARN")
            ragas_runtime_status = "init_failed"

    # Initialize Neo4j hybrid retriever only when requested.
    retriever = None
    if use_hybrid_rag:
        try:
            strategy = get_final_strategy()
            retriever = get_retriever_from_strategy(strategy)
            if retriever:
                log(f"Neo4j hybrid retriever initialized via strategy: {strategy.name}")
        except Exception as exc:
            if not RETRIEVAL_AVAILABLE:
                log("Hybrid RAG requested but retrieval strategy is not available.", "WARN")
            else:
                log(f"Neo4j hybrid retriever init failed: {exc}", "WARN")

    headers = [
        "topic", "age", "level", "model", "agent",
        "run_index", "seed", "repeat_count",
        "json_valid", "schema_compliance", "word_count",
        "examples_count", "readability", "lix_value", "content_coverage",
        "tone_encouragement", "tone_simplicity", "tone_engagement",
        "ragas_faithfulness", "ragas_answer_relevancy",
        "ragas_context_precision", "ragas_context_recall",
        "ragas_avg", "ragas_status",
        "hallucination_rate", "ttft_ms", "latency",
        "rag_score", "llm_score", "agent_score", "final_score",
        "response_length", "details",
        "pedagogical_graph_json",
    ]

    results: List[Dict[str, Any]] = []
    summary_results: List[Dict[str, Any]] = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for topic_cfg in config.topics:
        topic = topic_cfg["topic"]
        age = topic_cfg["age"]
        level = topic_cfg["level"]
        reference_answer = topic_cfg.get("reference_answer", "")
        module_id = topic_cfg.get("module_id")
        module_name = topic_cfg.get("module_name")
        module_index = topic_cfg.get("module_index")
        repeats = int(topic_cfg.get("repeats", 1) or 1)
        seed_base = topic_cfg.get("seed_base")

        graph_path = Path(pedagogical_graph_json) if pedagogical_graph_json else latest_graph_export(config.outputs_dir, topic, age)
        if not graph_path or not graph_path.exists():
            raise FileNotFoundError(
                f"No pedagogical graph JSON found for topic='{topic}' age={age}. "
                "Pass --pedagogical-graph-json or export a COMP3 graph first."
            )

        context_docs = build_pedagogical_context_documents(
            graph_path,
            module_id=module_id,
            module_name=module_name,
            module_index=module_index,
            retriever=retriever,
        )
        if not context_docs:
            raise ValueError(f"Pedagogical graph context is empty: {graph_path}")

        selected_module_title = get_selected_pedagogical_module_title(
            graph_path,
            module_id=module_id,
            module_name=module_name,
            module_index=module_index,
        ) or f"{topic} Introduction"

        context_block = format_context_for_prompt(context_docs)
        log(f"Using pedagogical graph context: {graph_path.name}")
        log(f"  Pedagogical context docs: {len(context_docs)}")

        for model in config.models:
            log(f"Testing {topic} with {model}")
            for repeat_index in range(repeats):
                # Use topic seed_base when provided, otherwise fall back to config.default_seed
                topic_seed = seed_base if seed_base is not None else config.default_seed
                run_seed = int(topic_seed) + repeat_index if topic_seed is not None else None
                if repeats > 1:
                    log(f"  Repeat {repeat_index + 1}/{repeats} (seed={run_seed if run_seed is not None else 'n/a'})")

                detected_language = detect_language_from_topic(topic, model=model)

                phase1_tests = [
                    ("architect", config.load_prompt(
                        "architect",
                        topic=topic,
                        age=age,
                        level=level,
                        language=detected_language,
                        context=context_block,
                    )),
                    ("writer", config.load_prompt(
                        "writer",
                        module_title=selected_module_title,
                        topic=topic,
                        age=age,
                        level=level,
                        language=detected_language,
                        index=0,
                        context=context_block,
                        tone_guideline=config.get_tone_guideline(age),
                        feedback="",
                    )),
                ]

                writer_content = ""

                for agent, prompt in phase1_tests:
                    log(f"  > {agent}")
                    max_tok = getattr(config, f"ollama_max_tokens_{agent}", 700)
                    agent_temp = config.writer_temperature if agent == "writer" else 0.0
                    response, latency, ttft_ms = call_ollama_api(
                        model,
                        prompt,
                        api_url=config.ollama_url,
                        max_tokens=max_tok,
                        timeout=config.ollama_timeout,
                        seed=run_seed,
                        temperature=agent_temp,
                    )

                    if not response:
                        log(f"    No response from {agent}", "WARN")
                        continue

                    if agent == "writer":
                        parsed = extract_json_from_text(response) or {}
                        if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                            parsed = parsed[0]
                        writer_content = parsed.get("content", "") if isinstance(parsed, dict) else ""

                    if agent == "architect":
                        metrics = architect_metrics(response, latency, level=level)
                    else:
                        ragas_scores = None
                        if ragas_evaluator is not None:
                            try:
                                ragas_scores = ragas_evaluator.evaluate_generation(
                                    question=f"Write a {level} module about {topic} for age {age}",
                                    answer=writer_content,
                                    context="\n\n".join(context_docs),
                                    ground_truth=reference_answer,
                                    context_docs=context_docs,
                                    topic=topic,
                                )
                            except Exception as exc:
                                log(f"    RAGAS eval failed: {exc}", "WARN")

                        metrics = writer_metrics(
                            response,
                            latency,
                            ragas_scores=ragas_scores,
                            topic=topic,
                            age=age,
                            level=level,
                            groq_api_key=ragas_evaluator.api_key if ragas_evaluator else None,
                        )

                    ragas_faith = ragas_scores.get("faithfulness") if (agent == "writer" and ragas_scores) else None
                    hallucination = compute_hallucination_rate(
                        response,
                        context_docs,
                        ragas_faithfulness=ragas_faith,
                        agent=agent,
                    )
                    llm_score = compute_llm_score(
                        json_valid=bool(metrics.get("json_valid")),
                        hallucination_rate=hallucination,
                        latency=latency,
                        ttft_ms=ttft_ms,
                    )
                    rag_score = compute_rag_score(ragas_scores) if agent == "writer" else None
                    final_score = compute_final_score(
                        agent_score=float(metrics.get("agent_score", 0)),
                        llm_score=llm_score,
                        rag_score=rag_score,
                    )

                    metrics.update({
                        "generated_content": response,
                        "ttft_ms": ttft_ms,
                        "llm_score": llm_score,
                        "rag_score": rag_score,
                        "final_score": final_score,
                    })

                    if agent == "writer":
                        metrics["hallucination_rate"] = hallucination

                    metrics["context_docs_count"] = len(context_docs)
                    results.append(build_result_row(
                        topic=topic,
                        model=model,
                        agent=agent,
                        metrics=metrics,
                        age=age,
                        level=level,
                        ragas_runtime_status=ragas_runtime_status if agent == "writer" else "n/a",
                        pedagogical_graph_json=str(graph_path),
                        run_index=repeat_index + 1,
                        seed=run_seed,
                        repeat_count=repeats,
                    ))

                    log(f"    agent={metrics['agent_score']} llm={llm_score} rag={rag_score} final={final_score}")

                content_snippet = writer_content[:2000] if writer_content else ""
                if not content_snippet:
                    log("  Writer content empty: enricher/critic without context", "WARN")

                enricher_prompt = config.load_prompt(
                    "enricher",
                    module_content=content_snippet,
                    age=age,
                    lang=detected_language,
                )
                critic_prompt = config.load_prompt(
                    "critic",
                    course_summary=content_snippet,
                    age=age,
                    language=detected_language,
                    topic=topic,
                )

                for agent, prompt in [("enricher", enricher_prompt), ("critic", critic_prompt)]:
                    log(f"  > {agent}")
                    max_tok = getattr(config, f"ollama_max_tokens_{agent}", 700)
                    response, latency, ttft_ms = call_ollama_api(
                        model,
                        prompt,
                        api_url=config.ollama_url,
                        max_tokens=max_tok,
                        timeout=config.ollama_timeout,
                        seed=run_seed,
                    )

                    if not response:
                        log(f"    No response from {agent}", "WARN")
                        continue

                    if agent == "enricher":
                        metrics = enricher_metrics(response, latency)
                    else:
                        metrics = critic_metrics(response, latency)

                    llm_score = compute_llm_score(
                        json_valid=bool(metrics.get("json_valid")),
                        hallucination_rate=0.0,
                        latency=latency,
                        ttft_ms=ttft_ms,
                    )
                    final_score = compute_final_score(
                        agent_score=float(metrics.get("agent_score", 0)),
                        llm_score=llm_score,
                        rag_score=None,
                    )

                    metrics.update({
                        "generated_content": response,
                        "ttft_ms": ttft_ms,
                        "llm_score": llm_score,
                        "rag_score": None,
                        "final_score": final_score,
                    })

                    results.append(build_result_row(
                        topic=topic,
                        model=model,
                        agent=agent,
                        metrics=metrics,
                        age=age,
                        level=level,
                        pedagogical_graph_json=str(graph_path),
                        run_index=repeat_index + 1,
                        seed=run_seed,
                        repeat_count=repeats,
                    ))

                    log(f"    agent={metrics['agent_score']} llm={llm_score} final={final_score}")

        summary_results = summarize_rows(results)

    output_dir = config.outputs_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    topic_label = config.topics[0]["topic"].replace(" ", "_") if config.topics else "topic"
    age_label = config.topics[0]["age"] if config.topics else 0
    level_label = config.topics[0]["level"] if config.topics else "level"
    output_path = output_dir / f"comp2_pedagogical_graph_{topic_label}_age{age_label}_{level_label}_{timestamp}.csv"
    summary_output_path = output_dir / f"comp2_pedagogical_graph_{topic_label}_age{age_label}_{level_label}_avg_{timestamp}.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key, "") for key in headers})

    with open(summary_output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in summary_results:
            writer.writerow({key: row.get(key, "") for key in headers})

    log(f"Saved: {output_path}")
    log(f"Saved: {summary_output_path}")

    aggregate: Dict[Any, Dict[str, List[float]]] = defaultdict(lambda: {"agent": [], "llm": [], "final": []})
    for result in results:
        key = (result["model"], result["agent"])
        aggregate[key]["agent"].append(float(result.get("agent_score", 0) or 0))
        aggregate[key]["llm"].append(float(result.get("llm_score", 0) or 0))
        aggregate[key]["final"].append(float(result.get("final_score", 0) or 0))

    log("=== SUMMARY ===")
    for (model, agent), scores in sorted(aggregate.items()):
        log(
            f"{model} | {agent}: agent={statistics.mean(scores['agent']):.1f}  "
            f"llm={statistics.mean(scores['llm']):.1f}  final={statistics.mean(scores['final']):.1f}"
        )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="COMP2 comparison using COMP3 pedagogical graph context"
    )
    parser.add_argument(
        "--models",
        type=str,
        default="mistral:latest,llama3.1:latest",
        help="Comma-separated list of models to test",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Python",
        help="Topic to generate course for",
    )
    parser.add_argument(
        "--age",
        type=int,
        default=12,
        help="Student age",
    )
    parser.add_argument(
        "--level",
        type=str,
        default="beginner",
        help="Learning level",
    )
    parser.add_argument(
        "--reference",
        type=str,
        default=None,
        help="Optional reference_answer text",
    )
    parser.add_argument(
        "--no-ragas",
        action="store_true",
        help="Disable RAGAS evaluation",
    )
    parser.add_argument(
        "--pedagogical-graph-json",
        type=str,
        default=None,
        help="Path to a COMP3 graph JSON export. If omitted, use the latest matching graph in outputs/.",
    )
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="Print the module list from the pedagogical graph and exit.",
    )
    parser.add_argument(
        "--module-id",
        type=str,
        default=None,
        help="Optional module id to benchmark on a single module from the pedagogical graph.",
    )
    parser.add_argument(
        "--module-index",
        type=int,
        default=None,
        help="Optional module index to benchmark on a single module from the pedagogical graph.",
    )
    parser.add_argument(
        "--module-name",
        type=str,
        default=None,
        help="Optional module name to benchmark on a single module from the pedagogical graph.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of repeated generations to average for each model.",
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=42,
        help="Optional base seed used as seed + repeat_index for repeated generations.",
    )
    parser.add_argument(
        "--temp-writer",
        type=float,
        default=0.6,
        help="Temperature for the writer agent (use >0 for storytelling/adaptation).",
    )
    parser.add_argument(
        "--disable-cache",
        action="store_true",
        help="Disable RAGAS and related caches for deterministic runs.",
    )
    parser.add_argument(
        "--hybrid-rag",
        action="store_true",
        help="Enable hybrid RAG retrieval (Neo4j/vector) to enrich pedagogical context from an external retriever.",
    )

    args = parser.parse_args()

    if args.list_modules:
        if not args.pedagogical_graph_json:
            raise ValueError("--list-modules requires --pedagogical-graph-json")
        graph_path = Path(args.pedagogical_graph_json)
        if not graph_path.exists():
            raise FileNotFoundError(f"Pedagogical graph JSON not found: {graph_path}")
        modules = list_pedagogical_modules(graph_path)
        log(f"Modules found in {graph_path.name}:")
        for module in modules:
            log(
                f"  [{module['order']}] {module['name']} | id={module['id']} | "
                f"concepts={module['concept_count']} objectives={module['objective_count']} exercises={module['exercise_count']}"
            )
        return

    config = Config()
    config.models = [m.strip() for m in args.models.split(",") if m.strip()]
    config.use_ragas = not args.no_ragas
    # Honor CLI cache toggle
    if args.disable_cache:
        config.ragas_cache_enabled = False
    # Writer temperature override
    config.writer_temperature = float(args.temp_writer)
    config.topics = [{
        "topic": args.topic,
        "age": args.age,
        "level": args.level,
        "reference_answer": args.reference or "",
        "module_id": args.module_id,
        "module_name": args.module_name,
        "module_index": args.module_index,
        "repeats": max(1, args.repeats),
        "seed_base": args.seed_base,
    }]

    run_pedagogical_comp2(
        config,
        pedagogical_graph_json=args.pedagogical_graph_json,
        use_hybrid_rag=args.hybrid_rag,
    )


if __name__ == "__main__":
    main()