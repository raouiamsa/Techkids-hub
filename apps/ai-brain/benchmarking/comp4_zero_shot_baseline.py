"""COMP4 Zero-Shot Baseline Benchmark.

Ce script teste les LLMs de base (ex: LLaMA 3.1) en Zero-Shot face au schéma
JSON complet et détaillé (`COMP2_JSON_SCHEMA.json`). Le but est de prouver
qu'un modèle non-fine-tuné est incapable de générer un JSON valide et conforme
à un schéma aussi complexe, tout en respectant le Graphe Pédagogique.

Ceci constitue la Baseline avant le Fine-Tuning.
"""

import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import jsonschema

AI_BRAIN_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_BRAIN_DIR))

from benchmarking.config import Config
from benchmarking.comp2_pedagogical_graph_comparison import (
    call_ollama_api,
    latest_graph_export,
    build_pedagogical_context_documents,
    format_context_for_prompt,
)
from utils import extract_json_from_text

def log(msg: str, level: str = "INFO") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def run_zero_shot_baseline():
    config = Config()
    benchmark_dir = Path(__file__).parent
    
    schema_path = benchmark_dir / "COMP2_JSON_SCHEMA.json"
    if not schema_path.exists():
        log(f"Schéma introuvable : {schema_path}", "ERROR")
        return
        
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            target_schema = json.load(f)
    except Exception as e:
        log(f"Erreur de lecture du schéma : {e}", "ERROR")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = config.outputs_dir / f"comp4_zero_shot_baseline_{timestamp}.csv"
    
    headers = [
        "model", "topic", "age", "latency_s", "ttft_ms", "response_length",
        "json_valid", "schema_compliance", "validation_error"
    ]
    
    results = []
    
    log(f"Démarrage de la Baseline Zero-Shot (Schéma de {len(json.dumps(target_schema))} bytes)")
    
    for topic_cfg in config.topics:
        topic = topic_cfg["topic"]
        age = topic_cfg["age"]
        
        # Charger le Graphe Pédagogique (Architect output)
        graph_path = latest_graph_export(config.outputs_dir, topic, age)
        if not graph_path or not graph_path.exists():
            log(f"Aucun graphe trouvé pour {topic} (Age {age}). Ignoré.", "WARN")
            continue
            
        context_docs = build_pedagogical_context_documents(graph_path)
        context_block = format_context_for_prompt(context_docs)
        
        prompt = config.load_prompt(
            "generator_zero_shot",
            topic=topic,
            age=age,
            level=topic_cfg.get("level", "beginner"),
            language="python", # Ou détecté dynamiquement si tu as detect_language_from_topic
            context=context_block,
            target_schema=json.dumps(target_schema, indent=2)
        )

        for model in config.models:
            log(f"Test de {model} sur le sujet '{topic}'...")
            
            # Paramètres généreux pour laisser le modèle essayer de cracher le gros JSON
            response, latency, ttft_ms = call_ollama_api(
                model=model,
                prompt=prompt,
                api_url=config.ollama_url,
                max_tokens=2500,  # Schéma très long !
                timeout=config.ollama_timeout,
                temperature=0.1,  # Température basse pour privilégier la structure
                enforce_json=True
            )
            
            if not response:
                log(f"Aucune réponse de {model}", "ERROR")
                continue
                
            json_valid = False
            schema_compliance = False
            validation_error = ""
            
            parsed = extract_json_from_text(response)
            if parsed:
                json_valid = True
                try:
                    jsonschema.validate(instance=parsed, schema=target_schema)
                    schema_compliance = True
                except jsonschema.exceptions.ValidationError as e:
                    schema_compliance = False
                    validation_error = str(e).split('\\n')[0][:200]  # Garder l'erreur courte
            else:
                validation_error = "JSON invalide ou malformé"
                
            row = {
                "model": model,
                "topic": topic,
                "age": age,
                "latency_s": round(latency, 2),
                "ttft_ms": round(ttft_ms, 2) if ttft_ms else "",
                "response_length": len(response),
                "json_valid": json_valid,
                "schema_compliance": schema_compliance,
                "validation_error": validation_error
            }
            results.append(row)
            
            log(f"  -> JSON Valide: {json_valid} | Conforme au Schéma: {schema_compliance}")
            if not schema_compliance and validation_error:
                log(f"  -> Erreur: {validation_error}", "WARN")

    # Exporter en CSV
    if results:
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(results)
        log(f"Résultats exportés dans : {output_csv}")
    else:
        log("Aucun résultat à exporter.", "WARN")

if __name__ == "__main__":
    run_zero_shot_baseline()
