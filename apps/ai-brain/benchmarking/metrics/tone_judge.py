# benchmarking/metrics/tone_judge.py
"""LLM-as-judge pour les métriques de ton pédagogique via Groq API.

- tone_encouragement : Le texte utilise-t-il un ton encourageant pour les enfants ?
- tone_engagement    : Le texte est-il engageant (histoires, questions, défis) ?
- tone_simplicity    : formule Flesch — académiquement standard

Cache MD5 local pour éviter les appels Groq redondants.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests

# ── Constantes ────────────────────────────────────────────────────────────────
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"    # Modèle rapide + gratuit pour le judge
GROQ_MAX_TOKENS = 120                  # Réponse JSON courte
GROQ_TEMPERATURE = 0.0                 # Déterministe

EXCERPT_MAX_CHARS = 1500               # Extrait max envoyé au judge

_CACHE_DIR: Optional[Path] = None


def _get_cache_dir() -> Path:
    """Résout le répertoire de cache (créé si absent)."""
    global _CACHE_DIR
    if _CACHE_DIR is None:
        _CACHE_DIR = Path(__file__).resolve().parents[1] / "cache"
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def _cache_path(text: str) -> Path:
    """Chemin du fichier cache basé sur MD5 du texte."""
    key = hashlib.md5(text[:EXCERPT_MAX_CHARS].encode()).hexdigest()
    return _get_cache_dir() / f"tone_{key}.json"


def _load_cache(text: str) -> Optional[Dict[str, float]]:
    path = _cache_path(text)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _save_cache(text: str, result: Dict[str, float]) -> None:
    try:
        _cache_path(text).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass  # Échec silencieux


# ── Prompt Judge ──────────────────────────────────────────────────────────────
_SYSTEM_PROMPT_TEMPLATE = (
    "Tu es un évaluateur pédagogique expert. "
    "Tu analyses des textes destinés à des enfants de {age} ans. "
    "Réponds UNIQUEMENT en JSON valide, sans texte avant ou après."
)

_USER_PROMPT_TEMPLATE = """Évalue ce texte pédagogique sur 2 dimensions. Score de 0 à 100.

DÉFINITIONS:
- encouragement (0-100): Le texte utilise-t-il un ton positif et motivant ? (bravo, super, tu peux le faire, c'est normal de se tromper, réessaie...)
- engagement (0-100): Le texte est-il captivant ? (histoires, métaphores, questions rhétoriques, défis, scénarios réels, humour adapté...)

TEXTE À ÉVALUER:
\"\"\"
{excerpt}
\"\"\"

RÉPONDS EXACTEMENT DANS CE FORMAT JSON:
{{"encouragement": <entier 0-100>, "engagement": <entier 0-100>}}"""


# ── Appel Groq ────────────────────────────────────────────────────────────────
def _call_groq_judge(excerpt: str, api_key: str, age: int = 12) -> Tuple[float, float]:
    """Appelle Groq et retourne (encouragement, engagement) entre 0 et 100."""
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT_TEMPLATE.format(age=age)},
            {"role": "user", "content": _USER_PROMPT_TEMPLATE.format(excerpt=excerpt)},
        ],
        "temperature": GROQ_TEMPERATURE,
        "max_tokens": GROQ_MAX_TOKENS,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"].strip()

    # Parser la réponse JSON
    match = re.search(r"\{[^}]+\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"JSON introuvable dans la réponse judge: {raw}")

    parsed = json.loads(match.group(0))
    encouragement = float(parsed.get("encouragement", 0))
    engagement = float(parsed.get("engagement", 0))
    return (
        max(0.0, min(100.0, encouragement)),
        max(0.0, min(100.0, engagement)),
    )


# ── API Publique ──────────────────────────────────────────────────────────────
def judge_tone(
    content: str,
    age: int = 12,
    api_key: Optional[str] = None,
    use_cache: bool = True,
) -> Dict[str, float]:
    """Évalue le ton d'un texte pédagogique via Groq LLM-as-judge.

    Args:
        content      : Texte complet du module généré.
        age          : Âge cible de l'enfant.
        api_key      : Clé API Groq (fallback sur GROQ_API_KEY env var).
        use_cache    : Si True, utilise le cache local MD5.

    Returns:
        Dict avec keys: encouragement, engagement (0.0–100.0 chacun).
        En cas d'erreur, retourne les fallback statiques.
    """
    resolved_key = api_key or os.getenv("GROQ_API_KEY", "")
    excerpt = content[:EXCERPT_MAX_CHARS].strip()

    if not excerpt:
        return {"encouragement": 0.0, "engagement": 0.0, "source": "empty"}

    # Cache hit
    if use_cache:
        cached = _load_cache(excerpt)
        if cached:
            return {**cached, "source": "cache"}

    if not resolved_key:
        # Fallback statique si pas de clé API
        return _static_fallback(content)

    try:
        enc, eng = _call_groq_judge(excerpt, resolved_key, age=age)
        result = {
            "encouragement": round(enc, 2),
            "engagement": round(eng, 2),
            "source": "groq",
        }
        if use_cache:
            _save_cache(excerpt, result)
        return result

    except Exception as e:
        print(f"[WARN] tone_judge Groq failed: {e} — fallback statique")
        return _static_fallback(content)


# ── Fallback Statique Bilingue ────────────────────────────────────────────────
_ENCOURAGEMENT_MARKERS = [
    # Français
    "bravo", "super", "excellent", "félicitations", "bien joué", "c'est normal",
    "réessaie", "continue", "tu peux", "courage", "génial", "parfait",
    "bonne idée", "pas de panique", "c'est bien",
    # Anglais
    "great", "awesome", "well done", "good job", "you can", "let's",
    "excellent", "try again", "keep going", "amazing",
]

_ENGAGEMENT_MARKERS = [
    # Français
    "imagine", "histoire", "aventure", "robot", "jeu", "défi", "mission",
    "scénario", "suppose que", "imagine que", "comme si", "par exemple",
    # Anglais
    "imagine", "story", "adventure", "game", "challenge", "mission",
]


def _static_fallback(text: str) -> Dict[str, float]:
    """Fallback statique bilingue si Groq indisponible."""
    lower = text.lower()
    enc = min(100.0, sum(10.0 for m in _ENCOURAGEMENT_MARKERS if m in lower))
    eng_found = sum(1 for m in _ENGAGEMENT_MARKERS if m in lower)
    question_bonus = 20.0 if "?" in text else 0.0
    eng = min(100.0, eng_found * 10.0 + question_bonus)
    return {
        "encouragement": round(enc, 2),
        "engagement": round(eng, 2),
        "source": "static_fallback",
    }
