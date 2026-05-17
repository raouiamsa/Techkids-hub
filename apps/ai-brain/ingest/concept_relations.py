# apps/ai-brain/ingest/concept_relations.py
"""
Concept Relationships Inference

Infers pedagogical relationships between concepts:
- Prerequisites: Which concepts must be learned before others
- Related concepts: Concepts that complement each other
- Concept sequencing: Optimal learning order
"""

from typing import Dict, List, Set, Tuple, Optional
import sys
from pathlib import Path

AI_BRAIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_BRAIN_DIR))

from benchmarking.comp3_pedagogical_graph import PedagogicalGraph, Concept


class ConceptRelationshipInferrer:
    """
    Infers relationships between concepts using heuristics and optional LLM.
    
    Strategies:
    1. Heuristic-based: Textual similarity, concept naming patterns
    2. LLM-based: Call LLM to infer logical prerequisites
    3. Hybrid: Try heuristics first, then LLM for uncertain cases
    """
    
    # Common prerequisite patterns (textual heuristics)
    PREREQUISITE_PATTERNS = {
        "Variables": [],                          # No prerequisites
        "Data Types": ["Variables"],
        "Operators": ["Variables"],
        "Conditionals": ["Variables", "Operators"],
        "Loops": ["Variables", "Conditionals"],
        "Functions": ["Variables", "Loops"],
        "Lists": ["Variables", "Loops"],
        "Dictionaries": ["Variables", "Loops"],
        "List Comprehension": ["Lists", "Loops", "Functions"],
        "File I/O": ["Variables", "Strings"],
        "OOP": ["Functions", "Variables"],
        "Classes": ["OOP", "Functions"],
        "Inheritance": ["Classes"],
        "Polymorphism": ["Inheritance", "Classes"],
        "Decorators": ["Functions"],
        "Async": ["Functions", "Loops"],
        "Testing": ["Functions", "Conditionals"],
        "Modules": ["Functions"],
        "Error Handling": ["Conditionals", "Functions"],
        "Recursion": ["Functions"],
        "Generators": ["Functions", "Loops"],
        "Context Managers": ["OOP", "Error Handling"],
    }
    
    def __init__(self, use_heuristic: bool = True, use_llm: bool = False):
        """
        Initialize inferrer.
        
        Args:
            use_heuristic: Use textual heuristics (faster)
            use_llm: Use LLM for inference (more accurate, slower)
        """
        self.use_heuristic = use_heuristic
        self.use_llm = use_llm
    
    def infer_prerequisites(self, concepts: List[str], topic: str = "") -> Dict[str, List[str]]:
        """
        Infer prerequisites for concepts.
        
        Args:
            concepts: List of concept names
            topic: Topic context (e.g., "Python", "Arduino")
        
        Returns:
            Dict mapping concept -> list of prerequisite concepts
        """
        prerequisites: Dict[str, List[str]] = {}
        
        for concept in concepts:
            prereqs = []
            
            # Try heuristic first
            if self.use_heuristic:
                prereqs = self._infer_by_heuristic(concept, concepts)
            
            # If heuristic didn't find anything and LLM enabled, try LLM
            if not prereqs and self.use_llm:
                prereqs = self._infer_by_llm(concept, concepts, topic)
            
            # Ensure prerequisites exist in concepts list
            valid_prereqs = [p for p in prereqs if p in concepts]
            prerequisites[concept] = valid_prereqs
        
        return prerequisites
    
    def _infer_by_heuristic(self, concept: str, available_concepts: List[str]) -> List[str]:
        """
        Infer prerequisites using textual patterns.
        
        Rules:
        1. Check PREREQUISITE_PATTERNS dictionary
        2. Check concept name for implicit dependencies (e.g., "Advanced X" → "X")
        3. Check concept definition keywords
        """
        # Direct lookup in patterns
        if concept in self.PREREQUISITE_PATTERNS:
            return self.PREREQUISITE_PATTERNS[concept]
        
        # Check for normalized name (case-insensitive)
        for pattern_concept, pattern_prereqs in self.PREREQUISITE_PATTERNS.items():
            if concept.lower() == pattern_concept.lower():
                return pattern_prereqs
        
        # Check for implicit patterns
        # E.g., "Advanced Loops" → ["Loops"]
        for available in available_concepts:
            if available.lower() in concept.lower() and available != concept:
                return [available]
        
        return []
    
    def _infer_by_llm(self, concept: str, available_concepts: List[str], topic: str = "") -> List[str]:
        """
        Infer prerequisites using LLM (not implemented yet).
        
        Would call LLM with prompt like:
        "For concept 'Loops' in Python, which of these are prerequisites: [variables, functions, etc]?"
        """
        # TODO: Implement LLM-based inference
        print(f"Warning: LLM-based inference not yet implemented for concept '{concept}'")
        return []
    
    def build_prerequisite_graph(self, graph: PedagogicalGraph) -> Dict[str, List[str]]:
        """
        Build prerequisite graph for all concepts in pedagogical graph.
        
        Args:
            graph: PedagogicalGraph instance
        
        Returns:
            Dict of concept prerequisites
        """
        concept_names = [c.name for c in graph.concepts.values()]
        prerequisites = self.infer_prerequisites(concept_names)
        
        # Map back to concept IDs
        concept_id_map = {c.name: c.concept_id for c in graph.concepts.values()}
        
        id_prerequisites: Dict[str, List[str]] = {}
        for concept_name, prereq_names in prerequisites.items():
            concept_id = concept_id_map.get(concept_name)
            if concept_id:
                prereq_ids = [concept_id_map.get(p) for p in prereq_names if p in concept_id_map]
                id_prerequisites[concept_id] = prereq_ids
        
        return id_prerequisites
    
    def check_prerequisite_validity(self, prerequisites: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
        """
        Check if prerequisite graph is valid (no cycles, no contradictions).
        
        Args:
            prerequisites: Dict mapping concept -> prerequisites
        
        Returns:
            (is_valid, list of problems)
        """
        problems = []
        
        # Check 1: No self-prerequisites
        for concept, prereqs in prerequisites.items():
            if concept in prereqs:
                problems.append(f"Concept '{concept}' is its own prerequisite")
        
        # Check 2: No cycles (simple detection)
        for concept in prerequisites:
            if self._has_cycle(concept, prerequisites, set()):
                problems.append(f"Cycle detected involving concept '{concept}'")
        
        # Check 3: No contradictions (if A -> B and B -> A, that's a problem)
        for concept1, prereqs1 in prerequisites.items():
            for prereq in prereqs1:
                if concept1 in prerequisites.get(prereq, []):
                    problems.append(f"Contradiction: '{concept1}' requires '{prereq}' and vice versa")
        
        return len(problems) == 0, problems
    
    def _has_cycle(self, concept: str, prerequisites: Dict[str, List[str]], visited: Set[str]) -> bool:
        """Check if concept has cycles in prerequisite graph."""
        if concept in visited:
            return True
        
        visited.add(concept)
        
        for prereq in prerequisites.get(concept, []):
            if self._has_cycle(prereq, prerequisites, visited.copy()):
                return True
        
        return False
    
    def get_learning_sequence(self, concepts: List[str], prerequisites: Dict[str, List[str]]) -> List[str]:
        """
        Generate optimal learning sequence from prerequisites.
        
        Topological sort: concepts with no prerequisites come first,
        then concepts whose prerequisites are satisfied, etc.
        
        Args:
            concepts: List of concept names
            prerequisites: Dict of prerequisites
        
        Returns:
            Ordered list of concepts (learning sequence)
        """
        # Build adjacency for topological sort
        in_degree = {c: len(prerequisites.get(c, [])) for c in concepts}
        sequence = []
        queue = [c for c in concepts if in_degree[c] == 0]
        
        while queue:
            # Sort queue alphabetically for deterministic ordering
            queue.sort()
            concept = queue.pop(0)
            sequence.append(concept)
            
            # Find concepts that depend on this one
            for other in concepts:
                if other not in sequence and concept in prerequisites.get(other, []):
                    in_degree[other] -= 1
                    if in_degree[other] == 0:
                        queue.append(other)
        
        # If we couldn't order all concepts, there's a cycle
        if len(sequence) != len(concepts):
            print(f"Warning: Could not order all concepts (likely contains cycles)")
            return concepts
        
        return sequence
    
    def recommend_module_structure(self, concepts: List[str], prerequisites: Dict[str, List[str]], 
                                  target_modules: int = 3) -> Dict[int, List[str]]:
        """
        Recommend how to group concepts into modules based on prerequisites.
        
        Strategy:
        - Level 0: Concepts with no prerequisites
        - Level 1: Concepts that only depend on Level 0
        - Level 2: Concepts that only depend on Level 0-1
        - Then group levels into target_modules
        
        Args:
            concepts: List of concept names
            prerequisites: Dict of prerequisites
            target_modules: Target number of modules
        
        Returns:
            Dict mapping module_index -> list of concepts
        """
        # Assign level to each concept
        levels: Dict[str, int] = {}
        
        for concept in concepts:
            if not prerequisites.get(concept, []):
                levels[concept] = 0
            else:
                prereq_levels = [levels.get(p, 0) for p in prerequisites.get(concept, []) if p in levels]
                levels[concept] = (max(prereq_levels) + 1) if prereq_levels else 0
        
        # Group by level
        level_groups: Dict[int, List[str]] = {}
        for concept, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(concept)
        
        # Distribute levels into target_modules
        num_levels = max(level_groups.keys()) + 1 if level_groups else 1
        concepts_per_module = max(1, (num_levels + target_modules - 1) // target_modules)
        
        modules: Dict[int, List[str]] = {}
        current_module = 0
        concepts_in_current = 0
        
        for level in sorted(level_groups.keys()):
            for concept in level_groups[level]:
                if current_module not in modules:
                    modules[current_module] = []
                modules[current_module].append(concept)
                concepts_in_current += 1
                
                # Move to next module if we've reached the target
                if concepts_in_current >= concepts_per_module and current_module < target_modules - 1:
                    current_module += 1
                    concepts_in_current = 0
        
        return modules
