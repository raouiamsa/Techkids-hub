# benchmarking/metrics/llm_score.py
"""Couche LLM et couche RAG du scoring COMP2.
Séparation des scores selon la méthodologie documentée :
  - RAG Score   : qualité du contexte récupéré (via RAGAS)
  - LLM Score   : comportement brut du modèle (format, hallucination, latence)
  - Agent Score : succès de la tâche métier (défini dans architect/writer/enricher/critic)
  - Final Score : 0.2 × RAG + 0.3 × LLM + 0.5 × Agent (pour writer)
                  0.3 × LLM + 0.7 × Agent (pour les autres agents)
"""

import os
import logging
import math
from typing import Dict, List, Optional

# Configure logging pour debug mode
logger = logging.getLogger(__name__)
DEBUG_HALLUCINATION = os.getenv("DEBUG_HALLUCINATION", "false").lower() == "true"


# ── Hallucination Rate ────────────────────────────────────────────────────────

# Mots vides FR+EN ignorés dans le calcul heuristique
_STOPWORDS = {
    # FR
    "le","la","les","de","du","des","un","une","et","en","au","aux",
    "ce","se","sa","son","ses","mon","ma","mes","qui","que","quoi",
    "dont","où","est","sont","était","avoir","être","faire","plus",
    "pour","par","sur","sous","dans","avec","sans","entre","vers",
    "aussi","très","bien","mais","ou","si","car","donc","or","ni",
    "pas","ne","il","elle","ils","elles","nous","vous","on","je","tu",
    # EN
    "the","a","an","is","are","was","were","be","been","being",
    "have","has","had","do","does","did","will","would","could","should",
    "may","might","shall","can","of","in","to","for","on","at","by",
    "from","with","and","or","but","not","this","that","these","those",
    "it","its","we","you","he","she","they","our","your","their",
    "about","which","when","where","how","what","who","all","any","each",
}


def compute_hallucination_rate(
    response_text: str,
    context_docs: List[str],
    ragas_faithfulness: Optional[float] = None,
    agent: str = "unknown",
) -> Optional[float]:
    """Calcule le taux d'hallucination du modèle avec logs optionnels.

    Stratégie :
    - Si RAGAS faithfulness disponible : hallucination = 1 - faithfulness  (précis)
    - Sinon : heuristique améliorée — overlap de mots de contenu (sans stop words).
      Retourne None si le contexte est trop petit pour être fiable (< 50 mots utiles).

    Args:
        response_text       : texte brut généré par le modèle
        context_docs        : liste des documents récupérés
        ragas_faithfulness  : score RAGAS faithfulness (0-1), si disponible
        agent               : nom de l'agent (pour logs)

    Returns:
        hallucination_rate ∈ [0.0, 1.0], ou None si non mesurable
    """
    # Priorité : RAGAS faithfulness
    if ragas_faithfulness is not None and isinstance(ragas_faithfulness, (int, float)) and math.isfinite(float(ragas_faithfulness)):
        h_rate = round(1.0 - float(ragas_faithfulness), 4)
        if DEBUG_HALLUCINATION:
            logger.info(f"  [{agent}] Hallucination via RAGAS: {h_rate} (faithfulness={ragas_faithfulness})")
        return h_rate

    # Pas de contexte → non mesurable
    if not context_docs or not response_text:
        if DEBUG_HALLUCINATION:
            logger.info(f"  [{agent}] No context/response: hallucination=None")
        return None

    def content_tokens(text: str) -> set:
        """Extrait les mots de contenu (longueur > 3, non stop-word, normalisé)."""
        tokens = set()
        for raw in text.lower().split():
            word = raw.strip(".,;:!?\"'()[]{}«»—-")
            if len(word) > 3 and word not in _STOPWORDS:
                tokens.add(word)
        return tokens

    context_text = " ".join(context_docs)
    context_tokens = content_tokens(context_text)

    # Si le contexte a moins de 50 mots utiles, l'heuristique est trop imprécise
    if len(context_tokens) < 50:
        if DEBUG_HALLUCINATION:
            logger.info(f"  [{agent}] Context too small ({len(context_tokens)} tokens < 50): hallucination=None")
        return None

    response_tokens = content_tokens(response_text)
    if not response_tokens:
        if DEBUG_HALLUCINATION:
            logger.info(f"  [{agent}] No response tokens: hallucination=None")
        return None

    hallucinated_tokens = {t for t in response_tokens if t not in context_tokens}
    not_in_context = len(hallucinated_tokens)
    h_rate = round(not_in_context / len(response_tokens), 4)
    
    if DEBUG_HALLUCINATION:
        logger.info(f"  [{agent}] Hallucination heuristic:")
        logger.info(f"    Context tokens: {len(context_tokens)}")
        logger.info(f"    Response tokens: {len(response_tokens)}")
        logger.info(f"    Hallucinated: {not_in_context}/{len(response_tokens)} = {h_rate}")
        if hallucinated_tokens:
            sample = list(hallucinated_tokens)[:10]
            logger.info(f"    Sample hallucinated words: {sample}")
    
    return h_rate


# ── LLM Score ─────────────────────────────────────────────────────────────────

def compute_llm_score(
    json_valid: bool,
    hallucination_rate: Optional[float],
    latency: float,
    ttft_ms: Optional[float] = None,
) -> float:
    """Calcule le LLM Score (0-100) : comportement brut du modèle.

    json_valid (format_score) est ici dans la couche LLM car il mesure
    la capacité du modèle à suivre une consigne de format — pas la qualité
    de la tâche pédagogique. Il n'est plus dans agent_score.

    Poids :
    - format_score       (40%) : json_valid → instruction following
    - hallucination_score(40%) : 1 - hallucination_rate
    - latency_score      (20%) : 0s→100, 120s→0 (linéaire)

    Args:
        json_valid        : True si la réponse est du JSON parsable
        hallucination_rate: 0.0 = aucune hallucination, 1.0 = tout halluciné
        latency           : latence totale en secondes
        ttft_ms           : Time-To-First-Token en ms (informatif, non scoré)

    Returns:
        llm_score entre 0.0 et 100.0
    """
    format_score = 100.0 if json_valid else 0.0
    
    # Si non mesurable (None), on ne pénalise pas le modèle par défaut (0.0)
    h_rate = hallucination_rate if hallucination_rate is not None else 0.0
    hallucination_score = max(0.0, 1.0 - h_rate) * 100.0
    
    latency_score = max(0.0, 100.0 - (latency / 120.0) * 100.0)

    llm_score = format_score * 0.4 + hallucination_score * 0.4 + latency_score * 0.2
    return round(min(100.0, llm_score), 2)


# ── RAG Score ─────────────────────────────────────────────────────────────────

def compute_rag_score(ragas_scores: Optional[Dict]) -> Optional[float]:
    """Calcule le RAG Score (0-100) depuis les métriques RAGAS.

    Poids :
    - faithfulness       (35%) : réponse ancrée dans le contexte
    - answer_relevancy   (35%) : réponse pertinente à la question
    - context_precision  (15%) : documents pertinents bien classés (si GT dispo)
    - context_recall     (15%) : toutes les infos du GT dans le contexte (si GT dispo)

    Args:
        ragas_scores : dict retourné par LocalRagasEvaluator.evaluate_generation()

    Returns:
        rag_score entre 0.0 et 100.0, ou None si RAGAS non disponible
    """
    if not ragas_scores:
        return None

    faithfulness = ragas_scores.get("faithfulness", 0.0)
    relevancy = ragas_scores.get("answer_relevancy", 0.0)
    precision = ragas_scores.get("context_precision")
    recall = ragas_scores.get("context_recall")

    if not isinstance(faithfulness, (int, float)) or not math.isfinite(float(faithfulness)):
        faithfulness = 0.0
    if not isinstance(relevancy, (int, float)) or not math.isfinite(float(relevancy)):
        relevancy = 0.0
    if isinstance(precision, (int, float)) and not math.isfinite(float(precision)):
        precision = None
    if isinstance(recall, (int, float)) and not math.isfinite(float(recall)):
        recall = None

    # Base (70% du score)
    score = float(faithfulness) * 35.0 + float(relevancy) * 35.0

    # Bonus si context metrics disponibles (GT fourni)
    if isinstance(precision, (int, float)):
        score += float(precision) * 15.0
    else:
        # Redistribuer les 15% sur faithfulness si pas de GT
        score += float(faithfulness) * 15.0

    if isinstance(recall, (int, float)):
        score += float(recall) * 15.0
    else:
        score += float(relevancy) * 15.0

    return round(min(100.0, score), 2)


# ── Final Score ───────────────────────────────────────────────────────────────

def compute_final_score(
    agent_score: float,
    llm_score: float,
    rag_score: Optional[float] = None,
) -> float:
    """Calcule le Final Score composite selon la formule du plan COMP2.

    Si RAG Score disponible (writer avec RAGAS) :
        Final = 0.2 × RAG + 0.3 × LLM + 0.5 × Agent

    Sinon (architect, enricher, critic) :
        Final = 0.3 × LLM + 0.7 × Agent

    Args:
        agent_score : score de la tâche métier (0-100)
        llm_score   : comportement brut du modèle (0-100)
        rag_score   : qualité du retrieval (0-100), None si non calculé

    Returns:
        final_score entre 0.0 et 100.0
    """
    if rag_score is not None:
        final = rag_score * 0.2 + llm_score * 0.3 + agent_score * 0.5
    else:
        final = llm_score * 0.3 + agent_score * 0.7

    return round(min(100.0, final), 2)
