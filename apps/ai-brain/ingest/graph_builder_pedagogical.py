# apps/ai-brain/ingest/graph_builder_pedagogical.py
"""
Graph Builder for Pedagogical Graph Structure

Builds pedagogical graph from LLM-generated course structure JSON
and stores it in Neo4j for querying and analysis.
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

AI_BRAIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_BRAIN_DIR))

from benchmarking.comp3_pedagogical_graph import (
    PedagogicalGraph,
    Module,
    Concept,
    LearningObjective,
    Exercise,
    ExerciseType,
)


class PedagogicalGraphBuilder:
    """
    Builds a pedagogical graph from LLM JSON output.
    """

    def __init__(self):
        self.graph: Optional[PedagogicalGraph] = None
        self.current_module_concepts: Dict[str, str] = {}  # concept_id -> name
        self.current_module_objectives: Dict[str, List[str]] = {}  # objective_id -> associated_concepts

    def build_from_json_string(
        self,
        json_str: str,
        topic: str,
        age: int,
        level: str
    ) -> PedagogicalGraph:
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from LLM: {e}")

        return self.build_from_dict(data, topic, age, level)

    def build_from_dict(
        self,
        data: Dict[str, Any],
        topic: str,
        age: int,
        level: str
    ) -> PedagogicalGraph:

        self.graph = PedagogicalGraph(
            topic=topic,
            age=age,
            level=level,
            language=data.get("language", "French"),
            model_name=data.get("model_name"),
        )

        for module_data in data.get("modules", []):
            self._process_module(module_data)

        self._build_concept_prerequisites(data.get("modules", []))

        return self.graph

    def _infer_concept_for_exercise(self, question: str, module_data: Dict[str, Any]) -> Optional[str]:
        """
        Infer which concept an exercise tests if tests_concept is missing.
        Uses simple keyword matching against concept names in the module.
        """
        question_lower = question.lower()
        concepts = module_data.get("concepts", [])
        
        if not concepts:
            return None
        
        # Score each concept by how many keywords from its name appear in question
        best_match = None
        best_score = 0
        
        for concept in concepts:
            concept_id = concept.get("concept_id")
            concept_name = concept.get("name", "").lower()
            
            if not concept_id or not concept_name:
                continue
            
            # Simple scoring: count how many words from concept name appear in question
            words = concept_name.split()
            score = sum(1 for word in words if word in question_lower)
            
            if score > best_score:
                best_score = score
                best_match = concept_id
        
        return best_match if best_score > 0 else None
    
    def _infer_objective_for_exercise(self, exercise_data: Dict[str, Any], module_data: Dict[str, Any]) -> Optional[str]:
        """
        Infer which objective an exercise tests if tests_objective is missing or
        inconsistent with the exercise concept.
        """
        objectives = module_data.get("learning_objectives", [])
        tests_concept = exercise_data.get("tests_concept")
        exercise_question = exercise_data.get("question", "").lower()
        exercise_type = str(exercise_data.get("type", "qcm")).lower()
        
        if not objectives:
            return None
        
        type_preferences = {
            "qcm": {"understand": 3, "apply": 1, "analyze": 0},
            "fill_blank": {"understand": 2, "apply": 2, "analyze": 0},
            "code": {"understand": 0, "apply": 3, "analyze": 2},
            "project": {"understand": 0, "apply": 2, "analyze": 3},
        }

        best_objective_id = None
        best_score = -1

        for obj in objectives:
            obj_id = obj.get("objective_id")
            if not obj_id:
                continue

            score = 0
            associated = obj.get("associated_concepts", [])
            objective_type = str(obj.get("type", "understand")).lower()
            description = str(obj.get("description", "")).lower()

            if tests_concept and tests_concept in associated:
                score += 10

            score += type_preferences.get(exercise_type, {}).get(objective_type, 0)

            # Lightweight lexical overlap between question text and objective description.
            description_words = [word for word in description.replace("-", " ").split() if len(word) > 3]
            score += sum(1 for word in description_words if word in exercise_question)

            if score > best_score:
                best_score = score
                best_objective_id = obj_id

        if best_objective_id:
            return best_objective_id

        first_obj = objectives[0] if objectives else None
        return first_obj.get("objective_id") if first_obj else None

    @staticmethod
    def _select_anchor_concept(target_name: str, candidate_ids: List[str], graph: PedagogicalGraph) -> Optional[str]:
        """
        Pick the most relevant anchor concept among candidates using a simple
        lexical overlap on concept names.
        """
        best_candidate = None
        best_score = -1

        target_lower = target_name.lower()

        for concept_id in candidate_ids:
            concept = graph.concepts.get(concept_id)
            if not concept:
                continue

            candidate_words = set(concept.name.lower().split())
            score = sum(1 for word in candidate_words if word in target_lower)

            if score > best_score:
                best_score = score
                best_candidate = concept_id

        return best_candidate or (candidate_ids[0] if candidate_ids else None)

    def _process_module(self, module_data: Dict[str, Any]) -> None:
        module_id = module_data.get(
            "module_id",
            f"m_{len(self.graph.modules) + 1}"
        )

        module = Module(
            module_id=module_id,
            name=module_data.get("name", "Unnamed Module"),
            description=module_data.get("description", ""),
            difficulty_level=module_data.get("difficulty", "beginner"),
            prerequisites_modules=module_data.get("prerequisites_module_ids", []),
            estimated_duration=module_data.get("duration_minutes", 60),
            order_in_curriculum=module_data.get("order", 0),
        )

        concept_ids = []

        for concept_data in module_data.get("concepts", []):
            concept_id = concept_data.get(
                "concept_id",
                f"c_{len(self.graph.concepts) + 1}"
            )

            concept_ids.append(concept_id)

            concept = Concept(
                concept_id=concept_id,
                name=concept_data.get("name", "Unnamed Concept"),
                definition=concept_data.get("definition", ""),
                difficulty_level=concept_data.get("difficulty", "beginner"),
                prerequisites=concept_data.get("prerequisites", []),
                related_concepts=concept_data.get("related_concepts", []),
                importance=concept_data.get("importance", 1.0),
            )

            self.graph.add_concept(concept)

        module.concepts = concept_ids

        objective_ids = []

        for obj_data in module_data.get("learning_objectives", []):
            obj_id = obj_data.get(
                "objective_id",
                f"obj_{len(self.graph.objectives) + 1}"
            )

            objective_ids.append(obj_id)

            obj = LearningObjective(
                objective_id=obj_id,
                objective_type=obj_data.get("type", "understand"),
                description=obj_data.get("description", ""),
                associated_concepts=obj_data.get("associated_concepts", []),
                assessment_criteria=obj_data.get("assessment_criteria"),
            )

            self.graph.add_objective(obj)

        module.learning_objectives = objective_ids

        exercise_ids = []

        for ex_data in module_data.get("exercises", []):
            ex_id = ex_data.get(
                "exercise_id",
                f"ex_{len(self.graph.exercises) + 1}"
            )

            exercise_ids.append(ex_id)

            ex_type_str = ex_data.get("type", "qcm")

            try:
                ex_type = ExerciseType(ex_type_str.lower())
            except Exception:
                ex_type = ExerciseType.QCM

            # Infer missing mappings (honest improvement: recover LLM oversights)
            tests_concept = ex_data.get("tests_concept")
            if not tests_concept:
                tests_concept = self._infer_concept_for_exercise(
                    ex_data.get("question", ""),
                    module_data
                )
            
            tests_objective = ex_data.get("tests_objective")
            if tests_objective:
                objective_lookup = {obj.get("objective_id"): obj for obj in module_data.get("learning_objectives", [])}
                objective_data = objective_lookup.get(tests_objective)
                if not objective_data or (tests_concept and tests_concept not in objective_data.get("associated_concepts", [])):
                    tests_objective = None

            if not tests_objective and (tests_concept or ex_data.get("question")):
                tests_objective = self._infer_objective_for_exercise(
                    {**ex_data, "tests_concept": tests_concept},
                    module_data
                )

            exercise = Exercise(
                exercise_id=ex_id,
                exercise_type=ex_type,
                question=ex_data.get("question", ""),
                answer=ex_data.get("correct_answer", ex_data.get("answer")),
                options=ex_data.get("options"),
                starter_code=ex_data.get("starter_code"),
                solution=ex_data.get("solution"),
                difficulty=ex_data.get("difficulty", "beginner"),
                tests_concept=tests_concept,
                tests_objective=tests_objective,
                estimated_time=ex_data.get("estimated_time_minutes", 5),
            )

            self.graph.add_exercise(exercise)

        module.exercises = exercise_ids

        self.graph.add_module(module)

    def _build_concept_prerequisites(
        self,
        modules_data: List[Dict[str, Any]]
    ) -> None:
        # Sort modules by declared order to avoid chaining prerequisites across
        # multiple levels. We keep prerequisite depth shallow by attaching later
        # concepts directly to root concepts from the first module.
        ordered_modules = [
            module_data for module_data in sorted(
                modules_data,
                key=lambda item: (item.get("order", 0), item.get("module_id", ""))
            )
            if module_data.get("module_id") in self.graph.modules
        ]

        if not ordered_modules:
            return

        first_module = self.graph.modules[ordered_modules[0]["module_id"]]
        root_concepts = [cid for cid in first_module.concepts if cid in self.graph.concepts]

        # Root concepts should not carry prerequisites.
        for root_id in root_concepts:
            root_concept = self.graph.concepts.get(root_id)
            if root_concept:
                root_concept.prerequisites = []
            self.graph.concept_prerequisites[root_id] = []

        if not root_concepts:
            return

        anchor_id = root_concepts[-1]

        for module_data in ordered_modules[1:]:
            module_id = module_data["module_id"]
            module = self.graph.modules[module_id]

            for concept_id in module.concepts:
                if concept_id not in self.graph.concepts:
                    continue

                concept = self.graph.concepts[concept_id]

                # Keep only direct prerequisites that point to a root concept.
                direct_prereqs = [
                    prereq_id
                    for prereq_id in self.graph.concept_prerequisites.get(concept_id, [])
                    if prereq_id in root_concepts and not self.graph.concept_prerequisites.get(prereq_id)
                ]

                if not direct_prereqs:
                    chosen_anchor = self._select_anchor_concept(concept.name, root_concepts, self.graph) or anchor_id
                    direct_prereqs = [chosen_anchor]
                else:
                    direct_prereqs = direct_prereqs[:1]

                concept.prerequisites = direct_prereqs
                self.graph.concept_prerequisites[concept_id] = direct_prereqs

    def save_to_json(self, output_path: Path) -> None:
        if not self.graph:
            raise ValueError("Graph not built yet")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.graph.to_json())

    def save_to_neo4j(self, neo4j_driver) -> None:
        if not self.graph:
            raise ValueError("Graph not built yet")

        with neo4j_driver.session() as session:

            for module in self.graph.modules.values():
                session.run(
                    """
                    CREATE (m:Module {
                        module_id: $id,
                        name: $name,
                        description: $desc,
                        difficulty_level: $diff,
                        order: $order
                    })
                    """,
                    id=module.module_id,
                    name=module.name,
                    desc=module.description,
                    diff=module.difficulty_level,
                    order=module.order_in_curriculum,
                )

            for concept in self.graph.concepts.values():
                session.run(
                    """
                    CREATE (c:Concept {
                        concept_id: $id,
                        name: $name,
                        definition: $definition,
                        difficulty_level: $diff
                    })
                    """,
                    id=concept.concept_id,
                    name=concept.name,
                    definition=concept.definition,
                    diff=concept.difficulty_level,
                )

            for cid, prereqs in self.graph.concept_prerequisites.items():
                for pid in prereqs:
                    session.run(
                        """
                        MATCH (a:Concept {concept_id: $pid}),
                              (b:Concept {concept_id: $cid})
                        CREATE (a)-[:PREREQUISITE_OF]->(b)
                        """,
                        cid=cid,
                        pid=pid,
                    )


def build_pedagogical_graph(
    json_str: str,
    topic: str,
    age: int,
    level: str
) -> PedagogicalGraph:

    builder = PedagogicalGraphBuilder()
    return builder.build_from_json_string(json_str, topic, age, level)