# benchmarking/comp3_structure_comparison.py
"""
COMP3 Simple vs Pedagogical Structure Comparison

Compares a flat/simple graph representation against the pedagogical graph
built from the same LLM-generated course structure.

Simple graph baseline:
- Resource -> Chunk -> Concept
- No explicit modules, objectives, or prerequisites

Pedagogical graph:
- Module -> Concept -> LearningObjective -> Exercise
- Explicit prerequisites and exercise-objective alignment

Usage:
    python comp3_structure_comparison.py --models mistral:latest,llama3.1:latest --topic "Python" --age 12 --level beginner
"""

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add project paths
AI_BRAIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_BRAIN_DIR))

from benchmarking.comp3_runner import Comp3Runner
from benchmarking.comp3_config import get_comp3_config
from benchmarking.metrics.comp3_graph_quality import Comp3GraphQualityMetrics
from ingest.graph_builder_pedagogical import build_pedagogical_graph


@dataclass
class SimpleGraphSnapshot:
    """Flat graph snapshot used as the simple baseline."""

    topic: str
    age: int
    level: str
    resources: int = 1
    chunks: int = 0
    concepts: int = 0
    exercises: int = 0
    resource_chunk_relations: int = 0
    chunk_concept_relations: int = 0
    mentioned_concepts: List[str] = field(default_factory=list)

    @property
    def node_count(self) -> int:
        return self.resources + self.chunks + self.concepts

    @property
    def relation_count(self) -> int:
        return self.resource_chunk_relations + self.chunk_concept_relations

    @property
    def density(self) -> float:
        if self.node_count == 0:
            return 0.0
        return self.relation_count / self.node_count

    @property
    def concept_coverage_pct(self) -> float:
        if self.concepts == 0:
            return 100.0
        return (len(set(self.mentioned_concepts)) / self.concepts) * 100

    @staticmethod
    def from_course_structure(course_json: Dict[str, Any], topic: str, age: int, level: str) -> "SimpleGraphSnapshot":
        """Build a simple graph snapshot from the same course JSON."""
        modules = course_json.get("modules", []) or []
        unique_concepts: List[str] = []
        mentioned_concepts: List[str] = []
        chunk_count = 0
        resource_chunk_relations = 0
        chunk_concept_relations = 0
        exercises_count = 0

        for module in modules:
            chunk_count += 1
            resource_chunk_relations += 1
            exercises = module.get("exercises", []) or []
            concepts = module.get("concepts", []) or []
            exercises_count += len(exercises)

            for concept in concepts:
                concept_id = str(concept.get("concept_id") or concept.get("name") or "").strip()
                if concept_id and concept_id not in unique_concepts:
                    unique_concepts.append(concept_id)
                if concept_id:
                    mentioned_concepts.append(concept_id)
                    chunk_concept_relations += 1

        return SimpleGraphSnapshot(
            topic=topic,
            age=age,
            level=level,
            resources=1,
            chunks=chunk_count,
            concepts=len(unique_concepts),
            exercises=exercises_count,
            resource_chunk_relations=resource_chunk_relations,
            chunk_concept_relations=chunk_concept_relations,
            mentioned_concepts=mentioned_concepts,
        )

    def density_score(self) -> float:
        """Score density on a 0-100 scale, preferring a moderate number of relations."""
        density = self.density
        if density == 0.0:
            return 0.0
        if 1.0 <= density <= 3.5:
            return 100.0
        if density < 1.0:
            return max(0.0, 100.0 - ((1.0 - density) * 35.0))
        return max(0.0, 100.0 - ((density - 3.5) * 25.0))

    def structure_score(self) -> float:
        """Overall score for the simple structure baseline."""
        return (self.concept_coverage_pct * 0.65) + (self.density_score() * 0.35)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "age": self.age,
            "level": self.level,
            "resources": self.resources,
            "chunks": self.chunks,
            "concepts": self.concepts,
            "exercises": self.exercises,
            "resource_chunk_relations": self.resource_chunk_relations,
            "chunk_concept_relations": self.chunk_concept_relations,
            "node_count": self.node_count,
            "relation_count": self.relation_count,
            "density": self.density,
            "concept_coverage_pct": self.concept_coverage_pct,
            "density_score": self.density_score(),
            "structure_score": self.structure_score(),
        }


@dataclass
class StructureComparisonResult:
    model: str
    topic: str
    age: int
    level: str
    latency: float
    simple: SimpleGraphSnapshot
    pedagogical_metrics: Dict[str, Any]
    pedagogical_graph_nodes: int
    pedagogical_graph_relations: int
    timestamp: str

    @property
    def simple_score(self) -> float:
        return self.simple.structure_score()

    @property
    def pedagogical_score(self) -> float:
        return float(self.pedagogical_metrics.get("overall_score", 0.0))

    @property
    def score_gap(self) -> float:
        return self.pedagogical_score - self.simple_score

    @property
    def recommendation(self) -> str:
        if self.score_gap >= 10.0:
            return "pedagogical"
        if self.score_gap <= -10.0:
            return "simple"
        return "tie"

    def to_row(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "topic": self.topic,
            "age": self.age,
            "level": self.level,
            "latency": self.latency,
            "simple_node_count": self.simple.node_count,
            "simple_relation_count": self.simple.relation_count,
            "simple_concept_coverage_pct": round(self.simple.concept_coverage_pct, 2),
            "simple_density": round(self.simple.density, 4),
            "simple_density_score": round(self.simple.density_score(), 2),
            "simple_structure_score": round(self.simple_score, 2),
            "pedagogical_node_count": self.pedagogical_graph_nodes,
            "pedagogical_relation_count": self.pedagogical_graph_relations,
            "pedagogical_concept_coverage_pct": round(float(self.pedagogical_metrics.get("concept_coverage_%", 0.0)), 2),
            "pedagogical_prerequisite_coherence_pct": round(float(self.pedagogical_metrics.get("prerequisite_coherence_%", 0.0)), 2),
            "pedagogical_exercise_objective_alignment_pct": round(float(self.pedagogical_metrics.get("exercise_objective_alignment_%", 0.0)), 2),
            "pedagogical_graph_density_score": round(float(self.pedagogical_metrics.get("graph_density_score", 0.0)), 2),
            "pedagogical_overall_score": round(self.pedagogical_score, 2),
            "score_gap": round(self.score_gap, 2),
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


class StructureComparator:
    """Compare a simple graph baseline against a pedagogical graph."""

    def __init__(self, runner: Optional[Comp3Runner] = None):
        self.runner = runner or Comp3Runner(get_comp3_config())
        self.config = self.runner.config

    def compare_model(self, model: str, topic: str, age: int, level: str) -> Optional[StructureComparisonResult]:
        """Generate a course once, then compare simple vs pedagogical structures."""
        generation = self.runner.generate_course_structure(model, topic, age, level)
        if not generation:
            return None

        course_json = generation["structure"]
        simple_snapshot = SimpleGraphSnapshot.from_course_structure(course_json, topic, age, level)

        pedagogical_graph = build_pedagogical_graph(
            json.dumps(course_json),
            topic=topic,
            age=age,
            level=level,
        )
        pedagogical_metrics = Comp3GraphQualityMetrics.compute_all(pedagogical_graph, self.config)

        pedagogical_nodes = len(pedagogical_graph.modules) + len(pedagogical_graph.concepts) + len(pedagogical_graph.objectives) + len(pedagogical_graph.exercises)
        pedagogical_relations = (
            sum(len(v) for v in pedagogical_graph.concept_prerequisites.values()) +
            sum(len(v) for v in pedagogical_graph.concept_exercises.values()) +
            sum(len(v) for v in pedagogical_graph.objective_concepts.values()) +
            sum(len(m.concepts) + len(m.learning_objectives) + len(m.exercises) + len(m.prerequisites_modules) for m in pedagogical_graph.modules.values())
        )

        return StructureComparisonResult(
            model=model,
            topic=topic,
            age=age,
            level=level,
            latency=generation["latency"],
            simple=simple_snapshot,
            pedagogical_metrics=pedagogical_metrics,
            pedagogical_graph_nodes=pedagogical_nodes,
            pedagogical_graph_relations=pedagogical_relations,
            timestamp=datetime.now().isoformat(),
        )

    def run(self, models: List[str], topic: str, age: int, level: str) -> List[StructureComparisonResult]:
        """Run comparison for a list of models."""
        print(f"\n{'='*72}")
        print(f"SIMPLE VS PEDAGOGICAL COMPARISON: {topic} (age {age}, {level})")
        print(f"{'='*72}")

        results: List[StructureComparisonResult] = []
        for model in models:
            print(f"\n[{model}]")
            start = time.time()
            result = self.compare_model(model, topic, age, level)
            if result is None:
                print("  skipped (generation or evaluation failed)")
                continue
            elapsed = time.time() - start
            print(f"  simple score:      {result.simple_score:.1f}")
            print(f"  pedagogical score: {result.pedagogical_score:.1f}")
            print(f"  score gap:         {result.score_gap:.1f}")
            print(f"  recommendation:    {result.recommendation}")
            print(f"  elapsed:           {elapsed:.2f}s")
            results.append(result)

        return results

    def export_csv(self, results: List[StructureComparisonResult], output_path: Optional[Path] = None) -> Optional[Path]:
        if not results:
            return None

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic = results[0].topic.replace(" ", "_")
            output_path = self.config.output_dir / f"comp3_structure_compare_{topic}_age{results[0].age}_level{results[0].level}_{timestamp}.csv"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "model",
            "topic",
            "age",
            "level",
            "latency",
            "simple_node_count",
            "simple_relation_count",
            "simple_concept_coverage_pct",
            "simple_density",
            "simple_density_score",
            "simple_structure_score",
            "pedagogical_node_count",
            "pedagogical_relation_count",
            "pedagogical_concept_coverage_pct",
            "pedagogical_prerequisite_coherence_pct",
            "pedagogical_exercise_objective_alignment_pct",
            "pedagogical_graph_density_score",
            "pedagogical_overall_score",
            "score_gap",
            "recommendation",
            "timestamp",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(result.to_row())

        print(f"\n✓ comparison CSV exported to {output_path.name}")
        return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare simple vs pedagogical graph structures")
    parser.add_argument("--models", type=str, default="mistral:latest,llama3.1:latest", help="Comma-separated model list")
    parser.add_argument("--topic", type=str, default="Python", help="Topic to generate")
    parser.add_argument("--age", type=int, default=12, help="Student age")
    parser.add_argument("--level", type=str, default="beginner", choices=["beginner", "intermediate", "advanced"], help="Learning level")
    parser.add_argument("--output", type=str, default="", help="Optional output CSV path")

    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    comparator = StructureComparator()
    results = comparator.run(models=models, topic=args.topic, age=args.age, level=args.level)

    if not results:
        print("No successful comparisons")
        return 1

    output_path = Path(args.output) if args.output else None
    comparator.export_csv(results, output_path=output_path)
    print("\n✓ Simple vs pedagogical comparison complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
