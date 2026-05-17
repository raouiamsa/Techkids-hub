# benchmarking/config.py
"""Configuration for COMP2 agents comparison."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class Config:
    """Central configuration for COMP2 benchmarking."""

    # Model configuration (phi3 removed due to high hallucination rates)
    models: List[str] = field(default_factory=lambda: ["mistral:latest", "llama3.1:latest"])

    # Test topics configuration
    topics: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "topic": "Python Variables",
            "age": 12,
            "level": "beginner",
            "reference_answer": "",
        },
        {
            "topic": "Python Loops",
            "age": 12,
            "level": "beginner",
            "reference_answer": "",
        },
        {
            "topic": "Python Functions",
            "age": 13,
            "level": "beginner",
            "reference_answer": "",
        },
        {
            "topic": "Python Lists",
            "age": 13,
            "level": "intermediate",
            "reference_answer": "",
        },
        {
            "topic": "Python Conditionals",
            "age": 12,
            "level": "beginner",
            "reference_answer": "",
        },
        {
            "topic": "Python OOP Basics",
            "age": 14,
            "level": "intermediate",
            "reference_answer": "",
        },
        {
            "topic": "Arduino LEDs",
            "age": 12,
            "level": "beginner",
            "reference_answer": "",
        },
        {
            "topic": "Web Development with HTML",
            "age": 13,
            "level": "beginner",
            "reference_answer": "",
        },
    ])

    # RAGAS configuration
    use_ragas: bool = True
    ragas_model: str = "llama-3.3-70b-versatile"
    ragas_cache_enabled: bool = True

    # Ollama configuration
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_timeout: int = 300
    ollama_max_tokens_architect: int = 3000
    ollama_max_tokens_writer: int = 3000
    ollama_max_tokens_enricher: int = 3000
    ollama_max_tokens_critic: int = 3000

    # Scoring weights (hardcoded per agent, documented below)
    # Architect: schema_compliance (30%) + module_count (20%) + module_completeness (20%) + pedagogical_structure (10%) + json_valid (20%)
    # Writer: schema_compliance (20%) + word_count (20%) + readability (15%) + richness (15%) + coverage (10%) + examples (10%) + tones (5%) + RAGAS (5%)
    # Enricher: schema_validity (20%) + options_validity (25%) + answer_index_validity (25%) + diversity (20%) + quantity (10%)
    # Critic: schema_compliance (25%) + score_range (25%) + consistency (25%) + issue_completeness (25%)

    # Paths (auto-configured)
    benchmarking_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    prompts_dir: Path = field(default_factory=lambda: Path(__file__).parent / "prompts")
    metrics_dir: Path = field(default_factory=lambda: Path(__file__).parent / "metrics")
    ragas_dir: Path = field(default_factory=lambda: Path(__file__).parent / "ragas")
    outputs_dir: Path = field(default_factory=lambda: Path(__file__).parent / "outputs")
    cache_dir: Path = field(default_factory=lambda: Path(__file__).parent / "cache")

    def __post_init__(self):
        """Ensure directories exist."""
        for dir_path in [self.outputs_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_tone_guideline(self, age: int) -> str:
        """Return dynamic tone instructions based on the student's age."""
        if age <= 9:
            return f"Tu parles à un enfant de {age} ans. Utilise des phrases très courtes (maximum 10 mots). Fais des analogies avec des animaux, des bonbons ou des jouets. Pose des questions directes à l'enfant et utilise beaucoup d'emojis. Le niveau de lecture doit être très facile et amusant."
        elif age <= 13:
            return f"Tu parles à un pré-ado de {age} ans. Utilise un langage dynamique, cool et interactif. Fais des analogies avec des jeux vidéos, le sport ou la vie au collège. Fais des phrases de longueur moyenne et garde un ton encourageant et motivant."
        else:
            return f"Tu parles à un adolescent de {age} ans. Utilise un langage mature, précis et professionnel. N'utilise surtout pas de ton enfantin. Fais des analogies avec le monde professionnel, les sciences appliquées ou la technologie réelle. Tu peux utiliser des phrases complexes et du vocabulaire technique approprié."

    def load_prompt(self, name: str, **kwargs) -> str:
        """Load and format a prompt template."""
        prompt_file = self.prompts_dir / f"{name}.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
        template = prompt_file.read_text(encoding="utf-8")
        return template.format(**kwargs)

    def get_cache_path(self, key: str) -> Path:
        """Get cache file path for a RAGAS evaluation."""
        import hashlib
        hash_val = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"ragas_{hash_val}.json"
