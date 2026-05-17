# benchmarking/metrics/comp3_graph_quality.py
"""
COMP3 Metrics for Pedagogical Graph Quality

Metrics:
1. Concept Coverage: % of concepts with exercises + objectives
2. Prerequisite Coherence: Validity and absence of cycles in prerequisite graph
3. Exercise-Objective Alignment: % of exercises properly linked to objectives
4. Graph Density: Relationships per concept (optimal: 2-5)

All metrics return values in range [0, 100] for consistency with COMP2.
"""

from typing import Dict, List, Set, Optional, Any
from benchmarking.comp3_pedagogical_graph import PedagogicalGraph
from benchmarking.comp3_config import Comp3Config

METRIC_KEYS = [
    "agent",
    "concept_coverage_%",
    "prerequisite_coherence_%",
    "exercise_objective_alignment_%",
    "graph_density_score",
    "graph_density_avg_relations",
    "has_cycles",
    "total_concepts",
    "covered_concepts",
    "total_exercises",
    "aligned_exercises",
    "latency",
    "model",
    "topic",
    "age",
    "level",
]


class ConceptCoverageMetric:
    @staticmethod
    def compute(graph: PedagogicalGraph, config: Comp3Config) -> Dict[str, Any]:
        if not graph.concepts:
            return {"score": 100.0, "covered": 0, "total": 0}

        total = len(graph.concepts)
        covered = 0

        for concept_id in graph.concepts:
            if graph.concept_exercises.get(concept_id):
                covered += 1

        score = (covered / total) * 100 if total else 0.0

        return {
            "score": score,
            "covered": covered,
            "total": total,
        }


class PrerequisiteCoherenceMetric:
    """
    Fixed cycle detection (proper DFS coloring: white/gray/black)
    """

    @staticmethod
    def _has_cycle_dfs(node: str, graph: PedagogicalGraph,
                       visiting: Set[str], visited: Set[str]) -> bool:
        visiting.add(node)

        for neigh in graph.concept_prerequisites.get(node, []):
            if neigh in visiting:
                return True
            if neigh not in visited:
                if PrerequisiteCoherenceMetric._has_cycle_dfs(neigh, graph, visiting, visited):
                    return True

        visiting.remove(node)
        visited.add(node)
        return False

    @staticmethod
    def has_cycle(graph: PedagogicalGraph) -> bool:
        visited = set()
        visiting = set()

        for concept_id in graph.concepts:
            if concept_id not in visited:
                if PrerequisiteCoherenceMetric._has_cycle_dfs(
                    concept_id, graph, visiting, visited
                ):
                    return True
        return False

    @staticmethod
    def _depth(graph: PedagogicalGraph, node: str, memo: Dict[str, int]) -> int:
        if node in memo:
            return memo[node]

        prereqs = graph.concept_prerequisites.get(node, [])
        if not prereqs:
            memo[node] = 0
            return 0

        depth = 1 + max(
            PrerequisiteCoherenceMetric._depth(graph, p, memo)
            for p in prereqs
        )

        memo[node] = depth
        return depth

    @staticmethod
    def compute(graph: PedagogicalGraph, config: Comp3Config) -> Dict[str, Any]:
        if not graph.concepts:
            return {"score": 100.0, "has_cycles": False}

        penalty = 0.0

        has_cycle = PrerequisiteCoherenceMetric.has_cycle(graph)
        if has_cycle:
            penalty += config.penalties.get("cycle", 40.0)

        constraints = config.pedagogical_constraints[graph.level]
        max_depth = constraints["prerequisite_depth"]
        max_prereq = constraints["max_prerequisites"]

        for cid, prereqs in graph.concept_prerequisites.items():
            if len(prereqs) > max_prereq:
                penalty += config.penalties.get("max_prerequisites_exceeded", 10.0)

        memo = {}
        for cid in graph.concepts:
            d = PrerequisiteCoherenceMetric._depth(graph, cid, memo)
            if d > max_depth:
                penalty += config.penalties.get("max_depth_exceeded", 20.0)

        score = max(0.0, 100.0 - penalty)

        return {
            "score": score,
            "has_cycles": has_cycle,
        }


class ExerciseObjectiveAlignmentMetric:
    @staticmethod
    def compute(graph: PedagogicalGraph, config: Comp3Config) -> Dict[str, Any]:
        if not graph.exercises:
            return {"score": 100.0, "aligned": 0, "total": 0}

        aligned = 0
        total = len(graph.exercises)

        for ex in graph.exercises.values():
            if ex.tests_objective and ex.tests_concept:
                obj = graph.objectives.get(ex.tests_objective)
                if obj and ex.tests_concept in obj.associated_concepts:
                    aligned += 1

        score = (aligned / total) * 100 if total else 0.0

        return {
            "score": score,
            "aligned": aligned,
            "total": total,
        }


class GraphDensityMetric:
    @staticmethod
    def compute(graph: PedagogicalGraph, config: Comp3Config) -> Dict[str, Any]:
        if not graph.concepts:
            return {"score": 100.0, "avg_relations": 0.0}

        counts = []

        for cid in graph.concepts:
            r = 0
            r += len(graph.concept_prerequisites.get(cid, []))

            for _, prereqs in graph.concept_prerequisites.items():
                if cid in prereqs:
                    r += 1

            r += len(graph.concept_exercises.get(cid, []))

            for obj in graph.objectives.values():
                if cid in obj.associated_concepts:
                    r += 1

            counts.append(r)

        avg = sum(counts) / len(counts)

        if 2 <= avg <= 5:
            score = 100.0
        elif avg < 2:
            score = max(0.0, 100.0 - (2 - avg) * 15)
        else:
            score = max(0.0, 100.0 - (avg - 5) * 10)

        return {
            "score": score,
            "avg_relations": avg,
        }


class Comp3GraphQualityMetrics:
    @staticmethod
    def compute_all(graph: PedagogicalGraph, config: Optional[Comp3Config] = None) -> Dict[str, Any]:
        if config is None:
            from benchmarking.comp3_config import get_comp3_config
            config = get_comp3_config()

        c1 = ConceptCoverageMetric.compute(graph, config)
        c2 = PrerequisiteCoherenceMetric.compute(graph, config)
        c3 = ExerciseObjectiveAlignmentMetric.compute(graph, config)
        c4 = GraphDensityMetric.compute(graph, config)

        return {
            "concept_coverage_%": c1["score"],
            "prerequisite_coherence_%": c2["score"],
            "exercise_objective_alignment_%": c3["score"],
            "graph_density_score": c4["score"],
            "overall_score": (
                c1["score"] * 0.25 +
                c2["score"] * 0.35 +
                c3["score"] * 0.25 +
                c4["score"] * 0.15
            )
        }