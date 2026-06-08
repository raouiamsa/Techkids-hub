# benchmarking/comp1_vanilla_llm_comparison.py
"""
COMP 1 Vanilla LLM Comparison (Simple Vector RAG Testbed)

Ce script correspond à la section 5.1.2.1 de la thèse (Model Selection).
Il évalue les LLMs (Mistral, LLaMA 3.1) en "Mode Vanille" (sans agents complexes)
en utilisant un RAG Vectoriel simple basé sur ChromaDB.
"""

import argparse
import csv
import json
import time
import os
import sys

# Fix pour les crashs silencieux de PyTorch/ChromaDB/Requests/HTTPX sur Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["CHROMA_TELEMETRY_IMPL"] = "chromadb.telemetry.dummy.DummyTelemetry"
os.environ["NO_PROXY"] = "*"  # Empêche la résolution WPAD
os.environ["HTTPX_NO_PROXIES"] = "1" # Empêche httpx de chercher un proxy
os.environ["RAGAS_DO_NOT_TRACK"] = "true"  # Désactive la télémétrie Ragas

import socket
_orig_getaddrinfo = socket.getaddrinfo
def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    host_str = host.decode('utf-8') if isinstance(host, bytes) else str(host)
    
    # Bypass total du DNS Windows pour les domaines critiques et WPAD
    if "api.groq.com" in host_str:
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('172.64.149.20', port))]
    if "localhost" in host_str or "wpad" in host_str:
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('127.0.0.1', port))]
        
    if family == 0:
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = patched_getaddrinfo

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Ajouter le dossier parent au PATH pour les imports
AI_BRAIN_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_BRAIN_DIR))

load_dotenv(dotenv_path=AI_BRAIN_DIR / ".env")

# Imports de l'application
from ingest.shared import EMBEDDINGS, CHROMA_PERSIST_DIR
from langchain_chroma import Chroma
from ragas_integration.evaluator import LocalRagasEvaluator

# ============================================================
# Logging
# ============================================================
def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

# ============================================================
# API Ollama
# ============================================================
def create_session_with_retries(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    session = requests.Session()
    session.trust_env = False  # Bypasses proxy resolution causing Windows getaddrinfo crashes
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
    api_url: str = "http://127.0.0.1:11434/api/generate",
    max_tokens: int = 1000,
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

    try:
        session = create_session_with_retries()
        with session.post(api_url, json=payload, stream=True, timeout=600) as response:
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

# ============================================================
# Main
# ============================================================
def run_vanilla_benchmark(models: List[str], use_ragas: bool = True):
    print("=> DEBUT DE run_vanilla_benchmark", flush=True)
    log("=== COMP 1 Vanilla LLM Comparison (Simple Vector RAG) ===")

    # 1. Initialiser ChromaDB
    log(f"Initialisation de ChromaDB depuis {CHROMA_PERSIST_DIR}...")
    try:
        vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=EMBEDDINGS
        )
        log("ChromaDB initialisé avec succès.")
    except Exception as e:
        log(f"Erreur d'initialisation de ChromaDB: {e}", "ERROR")
        return
        
    print("=> CHROMA INITIALISÉ", flush=True)

    # 2. Initialiser Ragas (Groq)
    ragas_evaluator = None
    if use_ragas:
        try:
            print("=> INITIALISATION RAGAS...", flush=True)
            ragas_evaluator = LocalRagasEvaluator(model="llama-3.3-70b-versatile")
            log("RAGAS evaluator initialisé (Groq).")
        except Exception as e:
            log(f"RAGAS init failed: {e}", "WARN")

    print("=> PRET POUR LE BENCHMARK", flush=True)

    # Sujets de test (basés sur le corpus)
    topics = [
        "Variables en Python (types, affectation, affichage)",
        "Circuits électriques en série et en parallèle",
        "Introduction à Arduino (microcontrôleur, broches, programmation)"
    ]

    results = []

    for topic in topics:
        log(f"\n--- Sujet : {topic} ---")
        
        # Retrieval (Vector RAG Simple)
        docs = vectorstore.similarity_search(topic, k=5)
        contexts = [doc.page_content for doc in docs]
        context_str = "\n\n".join(contexts)

        prompt = f"""Tu es un assistant utile.
En te basant UNIQUEMENT sur le contexte suivant, explique le sujet de manière claire et concise.

Contexte:
{context_str}

Sujet à expliquer: {topic}
"""

        for model in models:
            log(f"Test du modèle : {model}")
            answer, latency, ttft_ms = call_ollama_api(model=model, prompt=prompt)
            
            if not answer:
                log(f"Échec de la génération pour {model}", "ERROR")
                continue
                
            # Évaluation RAGAS
            faithfulness_score = 0.0
            answer_relevancy = 0.0
            if ragas_evaluator and contexts:
                try:
                    # On mesure la faithfulness (hallucination) et la pertinence
                    eval_results = ragas_evaluator.evaluate_generation(
                        question=topic,
                        answer=answer,
                        context=context_str,
                        context_docs=contexts,
                        topic=topic
                    )
                    faithfulness_score = eval_results.get("faithfulness", 0.0)
                    answer_relevancy = eval_results.get("answer_relevancy", 0.0)
                except Exception as e:
                    log(f"Erreur RAGAS pour {model}: {e}", "WARN")
            
            # Formater les résultats
            result_row = {
                "Topic": topic,
                "Model": model,
                "TTFT_ms": ttft_ms,
                "Latency_s": round(latency, 2),
                "Output_Length": len(answer),
                "Faithfulness_Ragas": round(faithfulness_score, 4),
                "Hallucination_Rate": round(1.0 - faithfulness_score, 4),
                "Answer_Relevance": round(answer_relevancy, 4),
            }
            results.append(result_row)
            log(f"Résultat {model} -> TTFT: {ttft_ms}ms | Faithfulness: {result_row['Faithfulness_Ragas']} | Relevance: {result_row['Answer_Relevance']}")

    # Sauvegarder en CSV
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = AI_BRAIN_DIR / "benchmarking" / "outputs"
        out_dir.mkdir(exist_ok=True)
        out_csv = out_dir / f"comp1_vanilla_llm_{timestamp}.csv"
        
        keys = results[0].keys()
        with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        
        log(f"\n[SUCCÈS] Résultats sauvegardés dans : {out_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="COMP 1 Vanilla LLM Comparison")
    parser.add_argument("--models", type=str, default="mistral:latest,llama3.1:latest", 
                        help="Modèles à tester séparés par une virgule")
    parser.add_argument("--no-ragas", action="store_true", help="Désactiver l'évaluation RAGAS")
    args = parser.parse_args()

    models_list = [m.strip() for m in args.models.split(",") if m.strip()]
    run_vanilla_benchmark(models=models_list, use_ragas=not args.no_ragas)
