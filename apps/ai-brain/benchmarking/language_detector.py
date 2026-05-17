"""
Language Auto-Detection Module for COMP2.
Uses LLM (Ollama) to intelligently detect programming language from topic.
Falls back to manual keyword matching if LLM is unavailable.
"""

import json
import re
import requests
from pathlib import Path
from typing import Dict, Optional

# Cache file for detected languages
LANGUAGE_CACHE_FILE = Path(__file__).resolve().parent / ".language_cache.json"

# Mapping: topic keywords → programming language (FALLBACK ONLY)
LANGUAGE_PATTERNS: Dict[str, list] = {
    "Python": [
        "python", "pandas", "numpy", "django", "flask", "machine learning",
        "data science", "scripting", "loops", "variables", "functions",
        "lists", "dictionaries", "oop basics", "classes", "inheritance",
    ],
    "JavaScript": [
        "javascript", "js", "react", "vue", "angular", "node", "nodejs",
        "web", "frontend", "dom", "async", "promises", "callbacks",
        "es6", "ecmascript", "browser", "typescript",
    ],
    "C++": [
        "c++", "cpp", "arduino", "embedded", "microcontroller", "systems",
        "pointers", "memory management", "oop c++", "stl", "competitive",
        "systems programming", "performance",
    ],
    "Java": [
        "java", "spring", "android", "applet", "jsp", "servlets",
        "enterprise", "android development", "oop java", "threads",
        "multithreading", "jvm",
    ],
    "SQL": [
        "sql", "database", "mysql", "postgresql", "queries", "joins",
        "schema", "normalization", "relational", "crud", "transactions",
        "indexes", "stored procedures",
    ],
    "HTML/CSS": [
        "html", "css", "styling", "markup", "responsive", "bootstrap",
        "tailwind", "flexbox", "grid", "web design", "semantics",
        "accessibility", "wcag",
    ],
    "Ruby": [
        "ruby", "rails", "ruby on rails", "gem", "rack", "sinatra",
        "metaprogramming", "duck typing", "conventions",
    ],
    "PHP": [
        "php", "laravel", "wordpress", "symfony", "yii", "server-side",
        "sessions", "cookies", "mysql php",
    ],
    "Go": [
        "go", "golang", "goroutine", "channel", "concurrent", "system",
        "microservices", "performance", "compile",
    ],
    "Rust": [
        "rust", "ownership", "borrow checker", "memory safety", "systems",
        "performance", "webassembly", "wasm",
    ],
    "Swift": [
        "swift", "ios", "macos", "app development", "cocoa", "swiftui",
        "optional", "playgrounds",
    ],
    "Kotlin": [
        "kotlin", "android kotlin", "coroutine", "null safety", "extension",
        "functional",
    ],
}

# Valid languages for validation
VALID_LANGUAGES = {
    "Python", "JavaScript", "C++", "Java", "SQL", "HTML/CSS",
    "Ruby", "PHP", "Go", "Rust", "Swift", "Kotlin", "TypeScript",
    "R", "MATLAB", "C#", "VB.NET", "Scala", "Clojure", "Perl",
}


def load_language_cache() -> Dict[str, str]:
    """Load cached language detections from disk."""
    if LANGUAGE_CACHE_FILE.exists():
        try:
            with open(LANGUAGE_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_language_cache(cache: Dict[str, str]):
    """Persist language cache to disk."""
    try:
        with open(LANGUAGE_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass  # Silent fail on cache write


def detect_language_from_topic_manual(topic: str) -> str:
    """
    Fallback manual detection using keyword matching.
    
    Args:
        topic: Topic name
    
    Returns:
        Detected language based on keywords
    """
    topic_lower = topic.lower()
    
    # Score each language based on keyword matches
    scores: Dict[str, int] = {}
    
    for language, keywords in LANGUAGE_PATTERNS.items():
        score = 0
        for keyword in keywords:
            # Exact word match (with word boundaries)
            if re.search(rf"\b{re.escape(keyword)}\b", topic_lower):
                score += 2
            # Substring match (lower priority)
            elif keyword in topic_lower:
                score += 1
        
        if score > 0:
            scores[language] = score
    
    # Return language with highest score, or Python as default
    if scores:
        detected = max(scores.items(), key=lambda x: x[1])[0]
        return detected
    
    return "Python"  # Safe default


def detect_language_from_topic(topic: str, model: Optional[str] = None) -> str:
    """
    Detect programming language from topic using LLM (Ollama).
    Uses cache for performance. Falls back to manual detection if LLM unavailable.
    
    Args:
        topic: Topic name (e.g., "Arduino LEDs", "Python Variables", "Web Development")
    
    Returns:
        Detected language (e.g., "C++", "Python", "HTML/CSS")
    
    Examples:
        >>> detect_language_from_topic("Arduino Blink LED")
        "C++"
        
        >>> detect_language_from_topic("React Components")
        "JavaScript"
        
        >>> detect_language_from_topic("SQL Joins")
        "SQL"
    
    Note:
        This function uses LLM for intelligent detection but falls back to
        manual keyword matching if Ollama is unavailable.
    """
    model_name = model or "mistral"
    cache_key = f"{model_name}::{topic}"

    # Check cache first
    cache = load_language_cache()
    if cache_key in cache:
        return cache[cache_key]
    
    # Try LLM detection
    language = _detect_language_with_llm(topic, model_name)
    
    # If LLM failed or returned invalid, fallback to manual
    if language not in VALID_LANGUAGES:
        language = detect_language_from_topic_manual(topic)
    
    # Cache the result
    cache[cache_key] = language
    save_language_cache(cache)
    
    return language


def _detect_language_with_llm(topic: str, model: str) -> str:
    """
    Call LLM (Ollama) to detect programming language from topic.
    
    Args:
        topic: Topic name
    
    Returns:
        Language name or empty string if detection failed
    """
    try:
        prompt = f"""Given this educational topic, what is the primary programming language that should be used to teach it?

Topic: {topic}

Answer with ONLY the language name (e.g., Python, C++, JavaScript, Java, SQL, HTML/CSS, Go, Rust, etc.).
If unsure, respond with the most appropriate language. Do not include explanations."""
        
        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            language = result.get("response", "").strip()
            
            # Extract just the language name (first line, remove extra text)
            language = language.split('\n')[0].strip()
            language = language.split(' ')[0].strip()  # First word only
            
            return language
    
    except requests.exceptions.ConnectionError:
        print(f"[LanguageDetector] Ollama unavailable (localhost:11434)")
    except requests.exceptions.Timeout:
        print(f"[LanguageDetector] Ollama timeout for topic '{topic}'")
    except Exception as e:
        print(f"[LanguageDetector] Error calling Ollama: {e}")
    
    # Return empty string to trigger manual fallback
    return ""


def detect_language_from_context(topic: str, context: str = "") -> str:
    """
    Detect language from topic (and optionally context).
    Currently uses topic-based detection. Context parameter reserved for future enhancement.
    
    Args:
        topic: Topic name
        context: Optional RAG context (for future use)
    
    Returns:
        Detected language
    """
    return detect_language_from_topic(topic)


if __name__ == "__main__":
    # Test examples
    test_cases = [
        "Arduino LEDs",
        "Python Variables",
        "React Components",
        "SQL Joins",
        "Web Development",
        "C++ Pointers",
        "Machine Learning",
        "Database Design",
    ]
    
    print("Language Detection Tests:")
    print("-" * 50)
    for topic in test_cases:
        detected = detect_language_from_topic(topic)
        print(f"Topic: {topic:30} → Language: {detected}")
