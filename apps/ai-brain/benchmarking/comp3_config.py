# benchmarking/comp3_config.py
"""Configuration for COMP3 pedagogical graph benchmarking."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class Comp3Config:
    """Configuration for COMP3 pedagogical graph quality assessment."""

    # Same models as COMP2 (for consistency)
    models: List[str] = field(default_factory=lambda: ["mistral:latest", "llama3.1:latest"])

    # Heuristic penalties for graph quality assessment
    penalties: Dict[str, float] = field(default_factory=lambda: {
        "cycle": 40.0,
        "max_depth_exceeded": 20.0,
        "max_prerequisites_exceeded": 10.0,
    })

    # Pedagogical level constraints
    pedagogical_constraints: Dict[str, Any] = field(default_factory=lambda: {
        "beginner": {
            "max_prerequisites": 1,           # Max prérequis par concept
            "modules_per_topic": 3,           # Diviser topic en max 3 modules
            "exercises_per_concept": 2,       # Min 2 exercices par concept
            "prerequisite_depth": 1,          # Max 1 niveau de profondeur
            "max_concepts_per_module": 5,     # Max 5 concepts par module
        },
        "intermediate": {
            "max_prerequisites": 2,
            "modules_per_topic": 4,
            "exercises_per_concept": 3,
            "prerequisite_depth": 2,
            "max_concepts_per_module": 7,
        },
        "advanced": {
            "max_prerequisites": 3,
            "modules_per_topic": 5,
            "exercises_per_concept": 4,
            "prerequisite_depth": 3,
            "max_concepts_per_module": 10,
        }
    })

    # Learning objectives templates by age
    learning_objectives_templates: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "age_12": {
            "understand": "L'étudiant comprend les concepts de base",
            "apply": "L'étudiant peut appliquer dans des cas simples",
            "analyze": "Non applicable",
        },
        "age_13": {
            "understand": "L'étudiant maîtrise les fondamentaux",
            "apply": "L'étudiant applique dans des contextes variés",
            "analyze": "L'étudiant analyse des exemples simples",
        },
        "age_16": {
            "understand": "L'étudiant maîtrise les fondamentaux avancés",
            "apply": "L'étudiant applique dans des projets réalistes",
            "analyze": "L'étudiant analyse et compare différentes approches",
        }
    })

    # Recommended learning sequences by topic and age
    learning_sequences: Dict[str, Dict[str, List[str]]] = field(default_factory=lambda: {
        "Python": {
            "age_12": [
                "Variables",
                "Data Types",
                "Operators",
                "Conditionals",
                "Loops",
                "Functions",
                "Lists"
            ],
            "age_13": [
                "Variables",
                "Data Types",
                "Functions",
                "Loops",
                "Dictionaries",
                "List Comprehension",
                "File I/O"
            ],
            "age_16": [
                "Variables",
                "OOP Basics",
                "Classes",
                "Inheritance",
                "Decorators",
                "Async/Await",
                "Testing"
            ]
        },
        "Arduino": {
            "age_12": [
                "Digital I/O",
                "Analog I/O",
                "Sensors",
                "Serial Communication",
                "Basic Projects"
            ],
            "age_13": [
                "Digital I/O",
                "Analog I/O",
                "Sensors",
                "Serial Communication",
                "Interrupts",
                "Timers"
            ],
            "age_16": [
                "Digital I/O",
                "Analog I/O",
                "Interrupts",
                "Timers",
                "Communication Protocols",
                "Advanced Projects"
            ]
        }
    })

    # Exercise type distribution by level
    exercise_type_distribution: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "beginner": {
            "qcm": 60,           # 60% QCM
            "code": 30,          # 30% code
            "fill_blank": 10,    # 10% fill-in-the-blank
            "project": 0,        # 0% projects
        },
        "intermediate": {
            "qcm": 40,
            "code": 40,
            "fill_blank": 15,
            "project": 5,
        },
        "advanced": {
            "qcm": 20,
            "code": 50,
            "fill_blank": 10,
            "project": 20,
        }
    })

    # Concept importance weights (how critical are prerequisites)
    concept_weights: Dict[str, float] = field(default_factory=lambda: {
        "Variables": 1.0,              # Foundation concepts (weight = 1.0)
        "Functions": 0.9,
        "Loops": 0.85,
        "Data Types": 0.8,
        "Conditionals": 0.85,
        "Lists": 0.7,
        "Dictionaries": 0.7,
        "OOP": 0.8,
        "Classes": 0.75,
        "Inheritance": 0.6,            # Advanced concepts (weight < 1.0)
        "Decorators": 0.5,
        "Async": 0.5,
    })

    generation_max_attempts: int = 2                    # Max attempts if concept coverage too low
    min_concept_coverage_ratio: float = 0.80            # Min % of concepts with exercises (0-1)
    generation_retry_timeout: int = 600                 # Timeout per generation attempt (seconds)

    def get_concept_weight(self, concept_id: str, graph_context: Any = None) -> float:
        """
        Dynamically calculate or retrieve the weight of a concept.
        If not in the hardcoded list, uses graph centrality heuristics.
        """
        if concept_id in self.concept_weights:
            return self.concept_weights[concept_id]
        
        # Fallback: estimate weight based on node out-degree (how many concepts depend on it)
        if graph_context and hasattr(graph_context, 'concept_prerequisites'):
            dependents = 0
            for cid, prereqs in graph_context.concept_prerequisites.items():
                if concept_id in prereqs:
                    dependents += 1
            # More dependents = higher foundational weight
            base_weight = 0.6
            bonus = min(0.4, dependents * 0.1)
            return round(base_weight + bonus, 2)
            
        return 0.7  # Default safe weight

    @property
    def output_dir(self) -> Path:
        """Output directory for COMP3 results."""
        return Path(__file__).parent / "outputs"

    @property
    def prompts_dir(self) -> Path:
        """Prompts directory for COMP3."""
        return Path(__file__).parent / "prompts"


def get_comp3_config() -> Comp3Config:
    """Factory function to get global COMP3 config."""
    return Comp3Config()
