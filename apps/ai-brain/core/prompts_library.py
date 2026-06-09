import os

# Chemin dynamique vers le dossier de benchmarking de la plateforme
PROMPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../benchmarking/prompts"))

def _load_prompt(filename: str) -> str:
    """Charge dynamiquement le contenu d'un fichier texte de prompt."""
    path = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Le fichier de prompt {filename} est introuvable dans {PROMPTS_DIR}.")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_architect_prompt(topic: str, age: int, level: str, language: str, context: str, module_count_instructions: str = "") -> str:
    """Importé de benchmarking/prompts/architect.txt"""
    template = _load_prompt("architect.txt")
    return template.format(
        topic=topic,
        age=age,
        level=level,
        language=language,
        context=context,
        module_count_instructions=module_count_instructions
    )

def get_writer_prompt(age: int, level: str, module_title: str, topic: str, language: str, context: str, tone_guideline: str, feedback: str, index: int) -> str:
    """Importé de benchmarking/prompts/writer.txt"""
    template = _load_prompt("writer.txt")
    return template.format(
        age=age,
        level=level,
        module_title=module_title,
        topic=topic,
        language=language,
        context=context,
        tone_guideline=tone_guideline,
        feedback=feedback,
        index=index
    )

def get_critic_prompt(module_title: str, content: str, language: str) -> str:
    """Importé de benchmarking/prompts/critic.txt"""
    template = _load_prompt("critic.txt")
    return template.format(
        module_title=module_title,
        content=content,
        language=language
    )

def get_enricher_prompt(module_title: str, content: str, language: str, age: int) -> str:
    """Importé de benchmarking/prompts/enricher.txt"""
    template = _load_prompt("enricher.txt")
    return template.format(
        module_title=module_title,
        content=content,
        language=language,
        age=age
    )

def get_pedagogical_extractor_prompt() -> str:
    """Importé de benchmarking/prompts/pedagogical_extractor.txt"""
    # Ce prompt n'a peut-être pas de variables de formatage directes s'il est utilisé dynamiquement
    return _load_prompt("pedagogical_extractor.txt")