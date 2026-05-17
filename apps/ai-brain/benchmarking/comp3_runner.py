# benchmarking/comp3_runner.py
"""
COMP3 Pedagogical Graph Benchmarking Tool

Orchestrates evaluation of pedagogical graph quality across multiple LLM models.

This tool:
1. Calls LLM with pedagogical_extractor prompt
2. Parses generated course structure JSON
3. Builds pedagogical graph
4. Computes all 4 COMP3 metrics
5. Exports results to CSV

Usage:
    python comp3_runner.py --models mistral:latest,llama3.1:latest --topic "Python" --age 12 --level beginner
"""

import argparse
import json
import csv
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add to path
AI_BRAIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_BRAIN_DIR))

from benchmarking.comp3_config import Comp3Config, get_comp3_config
from benchmarking.comp3_pedagogical_graph import PedagogicalGraph
from benchmarking.metrics.comp3_graph_quality import Comp3GraphQualityMetrics, METRIC_KEYS
from ingest.graph_builder_pedagogical import build_pedagogical_graph
from utils import extract_json_from_text


class Comp3Runner:
    """Main orchestrator for COMP3 benchmarking."""
    
    def __init__(self, config: Optional[Comp3Config] = None):
        """
        Initialize COMP3 runner.
        
        Args:
            config: COMP3Config instance (defaults to get_comp3_config())
        """
        self.config = config or get_comp3_config()
        self.results: List[Dict[str, Any]] = []
        self.session = self._create_session()
    
    @staticmethod
    def _create_session():
        """Create requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _validate_course_structure(self, course_json: Dict[str, Any]) -> tuple[bool, Optional[List[str]]]:
        """
        Validate that generated course structure covers all concepts with exercises.
        
        Returns:
            (is_valid, missing_concepts_list)
        """
        if "error" in course_json:
            return False, course_json.get("missing_concepts", ["unknown"])
        
        modules = course_json.get("modules", [])
        if not modules:
            return False, ["no_modules"]
        
        # Collect all concepts
        all_concept_ids = set()
        concepts_with_exercises = set()
        all_exercise_ids = {}  # exercise_id -> (tests_concept, tests_objective)
        all_objective_ids = set()
        
        for module in modules:
            # Collect objectives
            for obj in module.get("learning_objectives", []):
                all_objective_ids.add(obj.get("objective_id"))
            
            # Collect concepts
            for concept in module.get("concepts", []):
                concept_id = concept.get("concept_id")
                if concept_id:
                    all_concept_ids.add(concept_id)
            
            # Collect exercises and their mappings
            for exercise in module.get("exercises", []):
                ex_id = exercise.get("exercise_id")
                tests_concept = exercise.get("tests_concept")
                tests_objective = exercise.get("tests_objective")
                
                if ex_id and tests_concept:
                    all_exercise_ids[ex_id] = (tests_concept, tests_objective)
                    concepts_with_exercises.add(tests_concept)
        
        # Check: all concepts have at least one exercise
        missing_concepts = all_concept_ids - concepts_with_exercises
        if missing_concepts:
            return False, list(missing_concepts)
        
        # Check: all exercises have valid mappings
        for ex_id, (tests_concept, tests_objective) in all_exercise_ids.items():
            if tests_concept not in all_concept_ids:
                return False, [f"exercise_{ex_id}_invalid_concept_{tests_concept}"]
            if tests_objective and tests_objective not in all_objective_ids:
                return False, [f"exercise_{ex_id}_invalid_objective_{tests_objective}"]
        
        return True, None
    
    def _build_retry_prompt(self, prompt_template: str, missing_concepts: List[str], attempt: int) -> str:
        """Build a corrective prompt for retry."""
        missing_str = ", ".join(missing_concepts[:5])  # Show first 5
        correction_msg = f"\n\n[RETRY ATTEMPT {attempt}] Les concepts suivants manquent d'exercices: {missing_str}\nASSURE-TOI QUE CHAQUE CONCEPT A AU MOINS 1 EXERCICE ET QUE tests_concept + tests_objective SONT REMPLIS."
        return prompt_template + correction_msg

    def _build_compact_prompt(self, prompt_template: str) -> str:
        """Produce a compact version of the pedagogical prompt to reduce model work.

        This keeps the essential constraints but asks for shorter output: fewer modules,
        fewer exercises per module, and minimal textual descriptions to speed up generation.
        """
        compact_msg = (
            "\n\n[COMPACT MODE] Pour fiabiliser la génération, fournis une version plus concise du cours:\n"
            "- Nombre de modules: 2\n"
            "- Exercices par module: 1-2 (préférence 1)\n"
            "- Réponses et descriptions: très concises (une phrase max par définition)\n"
            "- Respecte toujours: chaque concept doit avoir au moins 1 exercice, tests_concept et tests_objective remplis.\n"
            "Réponds en JSON strict et minimise le texte libre."
        )
        return prompt_template + compact_msg
    
    def generate_course_structure(self, model: str, topic: str, age: int, level: str, language: str = "French") -> Optional[Dict[str, Any]]:
        """
        Call LLM to generate pedagogical course structure with validation and retry.
        
        Args:
            model: Model name (e.g., "mistral:latest")
            topic: Topic to generate (e.g., "Python")
            age: Student age
            level: Learning level
            language: Target language for the output (default "French")
        
        Returns:
            Parsed JSON structure or None on failure
        """
        # Load prompt template
        prompt_path = self.config.prompts_dir / "pedagogical_extractor.txt"
        if not prompt_path.exists():
            print(f"Error: Prompt file not found at {prompt_path}")
            return None
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Format prompt with parameters using replace to avoid JSON bracket conflicts
        base_prompt = prompt_template.replace("{topic}", topic).replace("{age}", str(age)).replace("{level}", level).replace("{language}", language)
        
        print(f"  Calling {model} to generate course structure for {topic} (age {age}, {level})...")
        
        total_latency = 0.0
        last_missing = ["generation_timeout"]
        
        for attempt in range(1, self.config.generation_max_attempts + 1):
            try:
                # Build prompt with corrections if retry
                if attempt > 1:
                    prompt = self._build_retry_prompt(base_prompt, last_missing, attempt)
                    print(f"  [Retry {attempt}/{self.config.generation_max_attempts}] Re-generating with corrections...")
                else:
                    prompt = base_prompt
                
                start_time = time.time()
                
                # Call Ollama via local API
                response = self.session.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_ctx": 4096,
                            "num_predict": 3000
                        }
                    },
                    timeout=self.config.generation_retry_timeout,
                )
                
                attempt_latency = time.time() - start_time
                total_latency += attempt_latency
                
                if response.status_code != 200:
                    print(f"  Error: LLM returned status {response.status_code}")
                    # try next attempt
                    if attempt >= self.config.generation_max_attempts:
                        break
                    continue
                
                result = response.json()
                response_text = result.get("response", "")
                
                # Extract JSON from response
                course_json = extract_json_from_text(response_text)
                
                if not course_json:
                    print(f"  Error: Could not extract JSON from LLM response (attempt {attempt})")
                    # try next attempt
                    if attempt >= self.config.generation_max_attempts:
                        break
                    continue
                
                # Validate structure
                is_valid, missing_concepts = self._validate_course_structure(course_json)
                
                if is_valid:
                    print(f"  ✓ Generated and validated successfully (attempt {attempt}, total latency: {total_latency:.2f}s)")
                    return {
                        "model": model,
                        "topic": topic,
                        "age": age,
                        "level": level,
                        "structure": course_json,
                        "latency": total_latency,
                    }
                else:
                    last_missing = missing_concepts or ["unknown"]
                    print(f"  ✗ Validation failed (attempt {attempt}): {', '.join(last_missing[:3])}")
                    if attempt >= self.config.generation_max_attempts:
                        print(f"  Error: Max generation attempts ({self.config.generation_max_attempts}) reached for normal mode. Will try compact mode before giving up.")
                        break
                    # Continue to next attempt
            
            except Exception as e:
                print(f"  Error generating course structure (attempt {attempt}): {e}")
                last_missing = ["generation_timeout"]
                if attempt >= self.config.generation_max_attempts:
                    print("  Max attempts reached for normal mode; will try compact prompt mode next.")
                    break
                continue
        # If we reach here without a successful generation, attempt a compact generation
        print("  Attempting COMPACT generation (shorter output requested) to improve success rate...")
        compact_prompt = self._build_compact_prompt(base_prompt)

        try:
            start_time = time.time()
            response = self.session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": compact_prompt,
                    "stream": False,
                },
                timeout=self.config.generation_retry_timeout,
            )
            total_latency += time.time() - start_time

            if response.status_code != 200:
                print(f"  Compact mode error: LLM returned status {response.status_code}")
                return None

            result = response.json()
            response_text = result.get("response", "")
            course_json = extract_json_from_text(response_text)

            if not course_json:
                print("  Compact mode: Could not extract JSON from LLM response")
                return None

            is_valid, missing_concepts = self._validate_course_structure(course_json)
            if is_valid:
                print(f"  ✓ Compact generation succeeded (total latency: {total_latency:.2f}s)")
                return {
                    "model": model,
                    "topic": topic,
                    "age": age,
                    "level": level,
                    "structure": course_json,
                    "latency": total_latency,
                }
            else:
                print(f"  Compact generation produced invalid structure: {missing_concepts}")
                return None

        except Exception as e:
            print(f"  Compact generation failed: {e}")
            return None
    
    def evaluate_course(self, generation_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluate generated course structure using COMP3 metrics.
        
        Args:
            generation_result: Result from generate_course_structure()
        
        Returns:
            Dictionary with metrics results
        """
        model = generation_result["model"]
        topic = generation_result["topic"]
        age = generation_result["age"]
        level = generation_result["level"]
        course_json = generation_result["structure"]
        latency = generation_result["latency"]
        
        print(f"  Computing COMP3 metrics for {model}...")
        
        try:
            # Build pedagogical graph
            graph = build_pedagogical_graph(
                json.dumps(course_json),
                topic=topic,
                age=age,
                level=level
            )
            
            # Compute all metrics
            metrics = Comp3GraphQualityMetrics.compute_all(graph, self.config)
            
            print(f"    ✓ Metrics computed: overall_score={metrics['overall_score']:.1f}")
            
            return {
                "model": model,
                "topic": topic,
                "age": age,
                "level": level,
                "metrics": metrics,
                "graph": graph,
                "latency": latency,
                "timestamp": datetime.now().isoformat(),
            }
        
        except Exception as e:
            print(f"    Error computing metrics: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_comparison(self, models: List[str], topic: str, age: int, level: str) -> List[Dict[str, Any]]:
        """
        Run full COMP3 comparison for given parameters.
        
        Args:
            models: List of model names
            topic: Topic to test
            age: Student age
            level: Learning level
        
        Returns:
            List of evaluation results
        """
        print(f"\n{'='*60}")
        print(f"COMP3 Evaluation: {topic} (age {age}, {level})")
        print(f"{'='*60}")
        
        results = []
        
        for model in models:
            print(f"\n[{model}]")
            
            # Generate course structure
            gen_result = self.generate_course_structure(model, topic, age, level)
            if not gen_result:
                print(f"  Skipping {model} (generation failed)")
                continue
            
            # Evaluate metrics
            eval_result = self.evaluate_course(gen_result)
            if not eval_result:
                print(f"  Skipping {model} (evaluation failed)")
                continue
            
            results.append(eval_result)
            self.results.append(eval_result)
        
        return results
    
    def export_results_csv(self, results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
        """
        Export results to CSV.
        
        Args:
            results: List of evaluation results
            output_path: Output file path (auto-generated if None)
        
        Returns:
            Path to created CSV file
        """
        if not results:
            print("No results to export")
            return None
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic = results[0]["topic"].replace(" ", "_")
            age = results[0]["age"]
            level = results[0]["level"]
            filename = f"comp3_{topic}_age{age}_level{level}_models-{timestamp}.csv"
            output_path = self.config.output_dir / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nExporting results to {output_path.name}...")
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=METRIC_KEYS)
            writer.writeheader()
            
            for result in results:
                row = {
                    "agent": "pedagogical_graph",
                    "model": result["model"],
                    "topic": result["topic"],
                    "age": result["age"],
                    "level": result["level"],
                    "concept_coverage_%": result["metrics"]["concept_coverage_%"],
                    "prerequisite_coherence_%": result["metrics"]["prerequisite_coherence_%"],
                    "exercise_objective_alignment_%": result["metrics"]["exercise_objective_alignment_%"],
                    "graph_density_score": result["metrics"]["graph_density_score"],
                    "latency": result["latency"],
                }
                writer.writerow(row)
        
        print(f"✓ Exported {len(results)} results to {output_path.name}")
        return output_path
    
    def export_graphs_json(self, results: List[Dict[str, Any]], output_dir: Optional[Path] = None) -> List[Path]:
        """
        Export complete pedagogical graphs to JSON files.
        
        Args:
            results: List of evaluation results
            output_dir: Output directory (defaults to config.output_dir)
        
        Returns:
            List of created file paths
        """
        if output_dir is None:
            output_dir = self.config.output_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = []
        
        for result in results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = result["model"].replace(":", "_").replace("/", "_")
            filename = f"graph_{result['topic']}_age{result['age']}_{model_name}_{timestamp}.json"
            filepath = output_dir / filename
            
            result["graph"].generated_at = datetime.now().isoformat()
            result["graph"].model_name = result["model"]
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result["graph"].to_json())
            
            saved_files.append(filepath)
            print(f"  ✓ Saved graph to {filepath.name}")
        
        return saved_files


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="COMP3 Pedagogical Graph Benchmarking Tool"
    )
    parser.add_argument(
        "--models",
        type=str,
        default="mistral:latest,llama3.1:latest",
        help="Comma-separated list of models to test"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Python",
        help="Topic to generate course for"
    )
    parser.add_argument(
        "--age",
        type=int,
        default=12,
        help="Student age"
    )
    parser.add_argument(
        "--level",
        type=str,
        default="beginner",
        choices=["beginner", "intermediate", "advanced"],
        help="Learning level"
    )
    parser.add_argument(
        "--export-graphs",
        action="store_true",
        help="Export pedagogical graphs to JSON"
    )
    
    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",")]
    
    runner = Comp3Runner()
    
    # Run comparison
    results = runner.run_comparison(
        models=models,
        topic=args.topic,
        age=args.age,
        level=args.level
    )
    
    if not results:
        print("No successful evaluations")
        return 1
    
    # Export CSV results
    csv_path = runner.export_results_csv(results)
    
    # Export graphs if requested
    if args.export_graphs:
        print("\nExporting pedagogical graphs...")
        runner.export_graphs_json(results)
    
    print(f"\n✓ COMP3 evaluation complete! Results: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
