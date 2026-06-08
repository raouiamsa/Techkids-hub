"""COMP4 Multi-Agent Baseline Benchmark.

Ce script teste les LLMs de base (ex: LLaMA 3.1) en Zero-Shot via une simulation
de la chaîne Multi-Agents (Architect -> Writer -> Enricher) face au schéma
JSON complet et détaillé (`COMP2_JSON_SCHEMA.json`). 

Il utilise les vrais prompts des agents (chargés depuis le dossier `prompts/`),
mais remplace dynamiquement leur petite sortie JSON par les exigences du
schéma géant de production, pour prouver que l'orchestration échoue sur un gros payload.
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
from benchmarking.comp2_pedagogical_graph_comparison import call_ollama_api
from utils import extract_json_from_text

TOPICS = [
    ("Python Variables", 12, "python"),
    ("Python Loops", 10, "python"),
    ("Python Conditionals", 14, "python"),
    ("Arduino Blink LED", 11, "arduino")
]

SCHEMA_PATH = Path(__file__).parent / "COMP2_JSON_SCHEMA.json"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def strip_old_json_from_prompt(full_prompt: str) -> str:
    """Coupe le prompt juste avant la section 'FORMAT JSON'."""
    if "FORMAT" in full_prompt:
        return full_prompt.split("FORMAT")[0].strip()
    return full_prompt.strip()

def run_multi_agent_baseline():
    config = Config()
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        target_schema = json.load(f)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = OUTPUT_DIR / f"comp4_multi_agent_baseline_{timestamp}.csv"

    print(f"[INFO] Démarrage de la Baseline Multi-Agents (Vrais Prompts) (Schéma: {len(json.dumps(target_schema))} bytes)")

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["model", "topic", "age", "latency_s", "json_valid", "schema_compliance", "validation_error"])

        model = "llama3.1:latest"

        for topic, age, domain in TOPICS:
            print(f"\n[INFO] Test de la chaîne Multi-Agents sur '{topic}'...")
            start_time = time.time()
            
            error_msg = ""
            final_json_obj = {}
            json_valid = False
            schema_compliance = False
            
            try:
                # -------------------------------------------------------------
                # AGENT 1: ARCHITECTE
                # -------------------------------------------------------------
                base_arch = config.load_prompt("architect", topic=topic, age=age, level="beginner", language=domain, context="[Simulated RAG Context for Baseline]")
                base_arch = strip_old_json_from_prompt(base_arch)
                
                prompt_arch = f"{base_arch}\n\n===================================\nFORMAT JSON STRICT REQUIS\n===================================\nTu dois générer un JSON valide avec UNIQUEMENT ces clés:\n- metadata (title, level, domain, age_group, estimated_duration, tags)\n- learning_objectives\n- summary (short, long)\nNe génère AUCUN texte avant ou après le JSON."
                
                res_arch, _, _ = call_ollama_api(model, prompt_arch, max_tokens=1000)
                json_arch = extract_json_from_text(res_arch) or {}
                final_json_obj.update(json_arch)
                print(f"  [+] Architecte terminé.")
                
                # -------------------------------------------------------------
                # AGENT 2: RÉDACTEUR
                # -------------------------------------------------------------
                base_writer = config.load_prompt("writer", module_title=topic, topic=topic, age=age, level="beginner", language=domain, index=1, context="[Simulated RAG Context]", tone_guideline="Fun and engaging", feedback="")
                base_writer = strip_old_json_from_prompt(base_writer)
                
                prompt_writer = f"{base_writer}\n\nVoici le plan généré par l'Architecte: {json.dumps(json_arch)}\n\n===================================\nFORMAT JSON STRICT REQUIS\n===================================\nTu dois générer un JSON valide avec UNIQUEMENT ces clés pour compléter le plan:\n- concept_cards\n- content (sections)\nNe génère AUCUN texte avant ou après le JSON."
                
                res_writer, _, _ = call_ollama_api(model, prompt_writer, max_tokens=2000)
                json_writer = extract_json_from_text(res_writer) or {}
                final_json_obj.update(json_writer)
                print(f"  [+] Rédacteur terminé.")

                # -------------------------------------------------------------
                # AGENT 3: ENRICHISSEUR
                # -------------------------------------------------------------
                content_snippet = json.dumps(json_writer.get("content", {}))[:1000]
                base_enricher = config.load_prompt("enricher", module_content=content_snippet, age=age, lang=domain)
                base_enricher = strip_old_json_from_prompt(base_enricher)
                
                prompt_enricher = f"{base_enricher}\n\nVoici le contenu du Rédacteur: {content_snippet}\n\n===================================\nFORMAT JSON STRICT REQUIS\n===================================\nTu dois générer un JSON valide avec UNIQUEMENT ces clés pour finaliser le module:\n- code_examples\n- visual_aids\n- quiz\n- exercises\n- warnings\n- call_to_action\nNe génère AUCUN texte avant ou après le JSON."
                
                res_enricher, _, _ = call_ollama_api(model, prompt_enricher, max_tokens=2000)
                json_enricher = extract_json_from_text(res_enricher) or {}
                final_json_obj.update(json_enricher)
                print(f"  [+] Enrichisseur terminé.")
                
                json_valid = True
                
                jsonschema.validate(instance=final_json_obj, schema=target_schema)
                schema_compliance = True
                
            except Exception as e:
                error_msg = str(e)[:250]
                
            latency = round(time.time() - start_time, 2)
            
            print(f"  [{topic}] JSON Valide: {json_valid} | Conforme au Schéma: {schema_compliance}")
            if error_msg:
                print(f"  Erreur: {error_msg}")
                
            writer.writerow([model, topic, age, latency, json_valid, schema_compliance, error_msg])

if __name__ == "__main__":
    run_multi_agent_baseline()
