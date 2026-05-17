#!/usr/bin/env python3
"""
Quick sanity check: Test single comparison manually before full benchmark run.

Usage:
    python test_single_comparison.py

This runs:
- 1 topic (Python Variables)
- 1 model (phi3:latest - fastest)
- NO RAGAS (skip for speed)
- All 4 agents (architect → writer → enricher → critic)
- Displays results for manual inspection

Typical runtime: 2-3 minutes (depending on local Ollama)
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent to path
AI_BRAIN_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_BRAIN_DIR))

from benchmarking.config import Config
from benchmarking.metrics import architect_metrics, writer_metrics, enricher_metrics, critic_metrics
from benchmarking.utils import extract_json_from_text


def log(msg: str, level: str = "INFO", color: str = ""):
    """Log with color and timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # ANSI colors
    colors = {
        "INFO": "\033[94m",    # Blue
        "OK": "\033[92m",      # Green
        "WARN": "\033[93m",    # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"
    }
    
    color_code = colors.get(level, "")
    reset = colors["RESET"]
    print(f"{color_code}[{timestamp}] [{level}]{reset} {msg}")


def call_ollama_test(model: str, prompt: str, max_tokens: int = 700) -> tuple[str | None, float]:
    """Call Ollama API for testing."""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    start = time.time()
    try:
        session = requests.Session()
        retry_strategy = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }
        
        response = session.post("http://localhost:11434/api/generate", json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        latency = time.time() - start
        return result.get("response", "").strip(), latency
    
    except Exception as e:
        log(f"Ollama error: {e}", "ERROR")
        return None, time.time() - start


def test_single_comparison():
    """Run single comparison test."""
    log("\n" + "="*70, "INFO")
    log("COMP2 Single Comparison Test (Manual Sanity Check)", "INFO")
    log("="*70, "INFO")
    
    # Initialize config
    config = Config()
    config.use_ragas = False  # Disable RAGAS for speed
    
    # Select single topic and model
    topic_cfg = config.topics[0]  # Python Variables
    model = config.models[0]      # phi3:latest
    
    log(f"\nTopic: {topic_cfg['topic']} (age={topic_cfg['age']}, level={topic_cfg['level']})", "INFO")
    log(f"Model: {model}", "INFO")
    log(f"RAGAS: Disabled (for speed)", "WARN")
    
    # Load prompts
    try:
        architect_prompt = config.load_prompt(
            "architect",
            topic=topic_cfg["topic"],
            age=topic_cfg["age"],
            level=topic_cfg["level"],
            language=topic_cfg["language"],
            context=""
        )
        log(f"\n✓ Architect prompt loaded ({len(architect_prompt)} chars)", "OK")
    except Exception as e:
        log(f"✗ Failed to load architect prompt: {e}", "ERROR")
        return False
    
    # ── Test Architect ──
    log(f"\n→ Calling Architect agent...", "INFO")
    arch_response, arch_latency = call_ollama_test(model, architect_prompt, max_tokens=config.ollama_max_tokens_architect)
    
    if not arch_response:
        log("✗ Architect failed to respond", "ERROR")
        return False
    
    arch_metrics = architect_metrics(arch_response, arch_latency)
    log(f"✓ Architect response ({len(arch_response)} chars, {arch_latency:.1f}s)", "OK")
    log(f"  Score: {arch_metrics['score']}/100", "OK")
    log(f"  Schema: {arch_metrics['schema_compliance']}, Modules: {arch_metrics['module_count']}", "OK")
    
    # Extract architect output for downstream
    arch_json = extract_json_from_text(arch_response) or {}
    if isinstance(arch_json, list) and arch_json and isinstance(arch_json[0], dict):
        arch_json = arch_json[0]
    
    # ── Test Writer ──
    log(f"\n→ Calling Writer agent...", "INFO")
    
    try:
        writer_prompt = config.load_prompt(
            "writer",
            module_title=f"{topic_cfg['topic']} Introduction",
            age=topic_cfg["age"],
            level=topic_cfg["level"],
            language=topic_cfg["language"],
            index=0,
            context="",
            feedback=""
        )
        log(f"✓ Writer prompt loaded ({len(writer_prompt)} chars)", "OK")
    except Exception as e:
        log(f"✗ Failed to load writer prompt: {e}", "ERROR")
        return False
    
    writer_response, writer_latency = call_ollama_test(model, writer_prompt, max_tokens=config.ollama_max_tokens_writer)
    
    if not writer_response:
        log("✗ Writer failed to respond", "ERROR")
        return False
    
    writer_metrics_result = writer_metrics(writer_response, writer_latency, topic=topic_cfg["topic"])
    log(f"✓ Writer response ({len(writer_response)} chars, {writer_latency:.1f}s)", "OK")
    log(f"  Score: {writer_metrics_result['score']}/100", "OK")
    log(f"  Word count: {writer_metrics_result['word_count']}, Readability: {writer_metrics_result['readability']:.1f}", "OK")
    log(f"  Tone: enc={writer_metrics_result['tone_encouragement']:.1f}, sim={writer_metrics_result['tone_simplicity']:.1f}, eng={writer_metrics_result['tone_engagement']:.1f}", "OK")
    
    # Extract writer content for enricher
    writer_json = extract_json_from_text(writer_response) or {}
    if isinstance(writer_json, list) and writer_json and isinstance(writer_json[0], dict):
        writer_json = writer_json[0]
    writer_content = writer_json.get("content", "")[:2000] if isinstance(writer_json, dict) else ""
    
    # ── Test Enricher ──
    log(f"\n→ Calling Enricher agent...", "INFO")
    
    try:
        enricher_prompt = config.load_prompt(
            "enricher",
            module_title=f"{topic_cfg['topic']} Introduction",
            content=writer_content,
            level=topic_cfg["level"],
            age=topic_cfg["age"]
        )
        log(f"✓ Enricher prompt loaded ({len(enricher_prompt)} chars)", "OK")
    except Exception as e:
        log(f"✗ Failed to load enricher prompt: {e}", "ERROR")
        return False
    
    enricher_response, enricher_latency = call_ollama_test(model, enricher_prompt, max_tokens=config.ollama_max_tokens_enricher)
    
    if not enricher_response:
        log("✗ Enricher failed to respond", "ERROR")
        return False
    
    enricher_metrics_result = enricher_metrics(enricher_response, enricher_latency)
    log(f"✓ Enricher response ({len(enricher_response)} chars, {enricher_latency:.1f}s)", "OK")
    log(f"  Score: {enricher_metrics_result['score']}/100", "OK")
    log(f"  Questions: {enricher_metrics_result.get('question_count', 0)}", "OK")
    
    # ── Test Critic ──
    log(f"\n→ Calling Critic agent...", "INFO")
    
    try:
        critic_prompt = config.load_prompt(
            "critic",
            module_title=f"{topic_cfg['topic']} Introduction",
            content=writer_content,
            level=topic_cfg["level"],
            age=topic_cfg["age"]
        )
        log(f"✓ Critic prompt loaded ({len(critic_prompt)} chars)", "OK")
    except Exception as e:
        log(f"✗ Failed to load critic prompt: {e}", "ERROR")
        return False
    
    critic_response, critic_latency = call_ollama_test(model, critic_prompt, max_tokens=config.ollama_max_tokens_critic)
    
    if not critic_response:
        log("✗ Critic failed to respond", "ERROR")
        return False
    
    critic_metrics_result = critic_metrics(critic_response, critic_latency)
    log(f"✓ Critic response ({len(critic_response)} chars, {critic_latency:.1f}s)", "OK")
    log(f"  Score: {critic_metrics_result['score']}/100", "OK")
    log(f"  Consistency: {critic_metrics_result.get('consistency_score', 0)}/100", "OK")
    
    # ── Summary ──
    log(f"\n" + "="*70, "INFO")
    log("Summary", "INFO")
    log("="*70, "INFO")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic_cfg["topic"],
        "model": model,
        "agents": {
            "architect": {
                "score": arch_metrics["score"],
                "latency": arch_latency,
                "schema_valid": arch_metrics["schema_compliance"]
            },
            "writer": {
                "score": writer_metrics_result["score"],
                "latency": writer_latency,
                "word_count": writer_metrics_result["word_count"]
            },
            "enricher": {
                "score": enricher_metrics_result["score"],
                "latency": enricher_latency,
                "valid": enricher_metrics_result.get("json_valid", False)
            },
            "critic": {
                "score": critic_metrics_result["score"],
                "latency": critic_latency,
                "valid": critic_metrics_result.get("schema_compliance", False)
            }
        },
        "total_latency": arch_latency + writer_latency + enricher_latency + critic_latency
    }
    
    # Print summary table
    print("\n┌─────────────┬────────┬──────────┬─────────────┐")
    print("│ Agent       │ Score  │ Latency  │ Status      │")
    print("├─────────────┼────────┼──────────┼─────────────┤")
    
    for agent, data in results["agents"].items():
        status = "✓ OK" if data["score"] > 30 else "✗ LOW"
        print(f"│ {agent:11} │ {data['score']:6.0f} │ {data['latency']:7.1f}s │ {status:11} │")
    
    print("└─────────────┴────────┴──────────┴─────────────┘")
    
    total = results["total_latency"]
    log(f"\nTotal time: {total:.1f}s (~{total/60:.1f}m)", "OK")
    
    # Check for critical failures
    critical_failures = [
        agent for agent, data in results["agents"].items()
        if data["score"] < 20
    ]
    
    if critical_failures:
        log(f"\n✗ Critical failures: {', '.join(critical_failures)}", "ERROR")
        log(f"Full results:\n{json.dumps(results, indent=2)}", "WARN")
        return False
    
    log(f"\n✓ All agents responded successfully!", "OK")
    log(f"✓ Ready for full benchmark run!", "OK")
    
    # Save results
    results_file = Path(__file__).parent / "test_results_single.json"
    results_file.write_text(json.dumps(results, indent=2))
    log(f"\n✓ Results saved to: {results_file}", "OK")
    
    return True


if __name__ == "__main__":
    try:
        success = test_single_comparison()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("\n\nTest interrupted by user", "WARN")
        sys.exit(130)
    except Exception as e:
        log(f"\nUnexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
