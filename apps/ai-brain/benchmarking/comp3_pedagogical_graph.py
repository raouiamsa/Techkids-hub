# benchmarking/comp3_pedagogical_graph.py
"""
COMP3 Pedagogical Graph Structure

Defines the data structures and relationships for a pedagogical graph
that includes modules, learning objectives, concepts, and exercises
with prerequisite relationships.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
import json


class ExerciseType(Enum):
    """Types of exercises that can be generated."""
    QCM = "qcm"
    CODE = "code"
    FILL_BLANK = "fill_blank"
    PROJECT = "project"


class RelationType(Enum):
    """Types of pedagogical relationships."""
    PREREQUISITE_OF = "prerequisite_of"      # Concept A is prerequisite of Concept B
    TAUGHT_BY = "taught_by"                  # Concept is taught by Learning Objective
    EVALUATED_BY = "evaluated_by"            # Concept is evaluated by Exercise
    CONTAINS = "contains"                    # Module contains Concept
    HAS_OBJECTIVE = "has_objective"          # Module has Learning Objective
    INCLUDES = "includes"                    # Module includes Exercise


@dataclass
class Exercise:
    """Single exercise in the pedagogical graph."""
    
    exercise_id: str
    exercise_type: ExerciseType
    question: str
    answer: Optional[str] = None
    options: Optional[List[str]] = None      # For QCM
    starter_code: Optional[str] = None       # For code exercises
    solution: Optional[str] = None           # For code exercises
    difficulty: str = "beginner"             # beginner, intermediate, advanced
    tests_concept: Optional[str] = None      # Which concept does this exercise test?
    tests_objective: Optional[str] = None    # Which objective does this test?
    estimated_time: int = 5                  # minutes
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.exercise_id,
            "type": self.exercise_type.value,
            "question": self.question,
            "answer": self.answer,
            "options": self.options,
            "starter_code": self.starter_code,
            "solution": self.solution,
            "difficulty": self.difficulty,
            "tests_concept": self.tests_concept,
            "tests_objective": self.tests_objective,
            "estimated_time": self.estimated_time,
        }


@dataclass
class LearningObjective:
    """Learning objective (what students should be able to do)."""
    
    objective_id: str
    objective_type: str                      # understand, apply, analyze, create
    description: str
    associated_concepts: List[str] = field(default_factory=list)
    assessment_criteria: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.objective_id,
            "type": self.objective_type,
            "description": self.description,
            "associated_concepts": self.associated_concepts,
            "assessment_criteria": self.assessment_criteria,
        }


@dataclass
class Concept:
    """Educational concept (e.g., "Variables", "Loops")."""
    
    concept_id: str
    name: str
    definition: str
    difficulty_level: str = "beginner"       # beginner, intermediate, advanced
    prerequisites: List[str] = field(default_factory=list)  # IDs of prerequisite concepts
    related_concepts: List[str] = field(default_factory=list)
    importance: float = 1.0                  # Weight for curriculum
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.concept_id,
            "name": self.name,
            "definition": self.definition,
            "difficulty_level": self.difficulty_level,
            "prerequisites": self.prerequisites,
            "related_concepts": self.related_concepts,
            "importance": self.importance,
        }


@dataclass
class Module:
    """A learning module (e.g., "Variables & Data Types")."""
    
    module_id: str
    name: str
    description: str
    difficulty_level: str = "beginner"
    concepts: List[str] = field(default_factory=list)           # Concept IDs
    learning_objectives: List[str] = field(default_factory=list)# Objective IDs
    exercises: List[str] = field(default_factory=list)          # Exercise IDs
    prerequisites_modules: List[str] = field(default_factory=list)  # Module IDs
    estimated_duration: int = 60                                 # minutes
    order_in_curriculum: int = 0                                 # Position in learning sequence
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.module_id,
            "name": self.name,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
            "concepts": self.concepts,
            "learning_objectives": self.learning_objectives,
            "exercises": self.exercises,
            "prerequisites_modules": self.prerequisites_modules,
            "estimated_duration": self.estimated_duration,
            "order_in_curriculum": self.order_in_curriculum,
        }


@dataclass
class PedagogicalGraph:
    """Complete pedagogical graph structure."""
    
    topic: str
    age: int
    level: str
    language: str = "Python"
    
    # Main entities
    modules: Dict[str, Module] = field(default_factory=dict)
    concepts: Dict[str, Concept] = field(default_factory=dict)
    objectives: Dict[str, LearningObjective] = field(default_factory=dict)
    exercises: Dict[str, Exercise] = field(default_factory=dict)
    
    # Relationships (can be inferred from entity fields, but stored explicitly for performance)
    concept_prerequisites: Dict[str, List[str]] = field(default_factory=dict)  # concept_id -> [prereq_ids]
    concept_exercises: Dict[str, List[str]] = field(default_factory=dict)      # concept_id -> [exercise_ids]
    objective_concepts: Dict[str, List[str]] = field(default_factory=dict)     # objective_id -> [concept_ids]
    
    # Metadata
    generated_at: Optional[str] = None
    model_name: Optional[str] = None
    
    def add_module(self, module: Module) -> None:
        """Add a module to the graph."""
        self.modules[module.module_id] = module
    
    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the graph."""
        self.concepts[concept.concept_id] = concept
        if concept.concept_id not in self.concept_prerequisites:
            self.concept_prerequisites[concept.concept_id] = concept.prerequisites
    
    def add_objective(self, objective: LearningObjective) -> None:
        """Add a learning objective to the graph."""
        self.objectives[objective.objective_id] = objective
        if objective.objective_id not in self.objective_concepts:
            self.objective_concepts[objective.objective_id] = objective.associated_concepts
    
    def add_exercise(self, exercise: Exercise) -> None:
        """Add an exercise to the graph."""
        self.exercises[exercise.exercise_id] = exercise
        if exercise.tests_concept:
            if exercise.tests_concept not in self.concept_exercises:
                self.concept_exercises[exercise.tests_concept] = []
            self.concept_exercises[exercise.tests_concept].append(exercise.exercise_id)
    
    def link_concept_prerequisite(self, concept_id: str, prerequisite_id: str) -> None:
        """Add a prerequisite relationship between concepts."""
        if concept_id not in self.concept_prerequisites:
            self.concept_prerequisites[concept_id] = []
        if prerequisite_id not in self.concept_prerequisites[concept_id]:
            self.concept_prerequisites[concept_id].append(prerequisite_id)
    
    def get_concept_coverage(self) -> float:
        """
        Calculate percentage of concepts that have exercises.
        Range: 0.0 to 1.0
        """
        if not self.concepts:
            return 0.0
        
        covered_concepts = 0
        for concept_id in self.concepts:
            if concept_id in self.concept_exercises and self.concept_exercises[concept_id]:
                covered_concepts += 1
        
        return covered_concepts / len(self.concepts)
    
    def get_exercise_objective_alignment(self) -> float:
        """
        Calculate percentage of exercises properly aligned with objectives.
        Range: 0.0 to 1.0
        """
        if not self.exercises:
            return 1.0
        
        aligned = 0
        for exercise in self.exercises.values():
            # An exercise is aligned if:
            # 1. It tests a concept (tests_concept is set)
            # 2. It tests an objective (tests_objective is set)
            # 3. The concept is associated with that objective
            if exercise.tests_concept and exercise.tests_objective:
                if exercise.tests_objective in self.objective_concepts:
                    if exercise.tests_concept in self.objective_concepts[exercise.tests_objective]:
                        aligned += 1
            elif exercise.tests_concept or exercise.tests_objective:
                # Partial alignment (has one but not the other)
                aligned += 0.5
        
        return aligned / len(self.exercises)
    
    def to_dict(self) -> Dict:
        """Convert entire graph to dictionary for JSON serialization."""
        return {
            "topic": self.topic,
            "age": self.age,
            "level": self.level,
            "language": self.language,
            "generated_at": self.generated_at,
            "model_name": self.model_name,
            "modules": {k: v.to_dict() for k, v in self.modules.items()},
            "concepts": {k: v.to_dict() for k, v in self.concepts.items()},
            "objectives": {k: v.to_dict() for k, v in self.objectives.items()},
            "exercises": {k: v.to_dict() for k, v in self.exercises.items()},
            "relationships": {
                "concept_prerequisites": self.concept_prerequisites,
                "concept_exercises": self.concept_exercises,
                "objective_concepts": self.objective_concepts,
            }
        }
    
    def to_json(self) -> str:
        """Serialize graph to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @staticmethod
    def from_dict(data: Dict) -> "PedagogicalGraph":
        """Deserialize graph from dictionary."""
        graph = PedagogicalGraph(
            topic=data["topic"],
            age=data["age"],
            level=data["level"],
            language=data.get("language", "Python"),
            generated_at=data.get("generated_at"),
            model_name=data.get("model_name"),
        )
        
        # Reconstruct modules, concepts, objectives, exercises
        for module_data in data.get("modules", {}).values():
            module = Module(
                module_id=module_data["id"],
                name=module_data["name"],
                description=module_data["description"],
                difficulty_level=module_data.get("difficulty_level", "beginner"),
                concepts=module_data.get("concepts", []),
                learning_objectives=module_data.get("learning_objectives", []),
                exercises=module_data.get("exercises", []),
                prerequisites_modules=module_data.get("prerequisites_modules", []),
                estimated_duration=module_data.get("estimated_duration", 60),
                order_in_curriculum=module_data.get("order_in_curriculum", 0),
            )
            graph.add_module(module)
        
        for concept_data in data.get("concepts", {}).values():
            concept = Concept(
                concept_id=concept_data["id"],
                name=concept_data["name"],
                definition=concept_data["definition"],
                difficulty_level=concept_data.get("difficulty_level", "beginner"),
                prerequisites=concept_data.get("prerequisites", []),
                related_concepts=concept_data.get("related_concepts", []),
                importance=concept_data.get("importance", 1.0),
            )
            graph.add_concept(concept)
        
        for objective_data in data.get("objectives", {}).values():
            objective = LearningObjective(
                objective_id=objective_data["id"],
                objective_type=objective_data["type"],
                description=objective_data["description"],
                associated_concepts=objective_data.get("associated_concepts", []),
                assessment_criteria=objective_data.get("assessment_criteria"),
            )
            graph.add_objective(objective)
        
        for exercise_data in data.get("exercises", {}).values():
            exercise = Exercise(
                exercise_id=exercise_data["id"],
                exercise_type=ExerciseType(exercise_data["type"]),
                question=exercise_data["question"],
                answer=exercise_data.get("answer"),
                options=exercise_data.get("options"),
                starter_code=exercise_data.get("starter_code"),
                solution=exercise_data.get("solution"),
                difficulty=exercise_data.get("difficulty", "beginner"),
                tests_concept=exercise_data.get("tests_concept"),
                tests_objective=exercise_data.get("tests_objective"),
                estimated_time=exercise_data.get("estimated_time", 5),
            )
            graph.add_exercise(exercise)
        
        return graph
