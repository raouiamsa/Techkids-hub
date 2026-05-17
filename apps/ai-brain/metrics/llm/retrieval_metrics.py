import numpy as np
import re
from typing import List, Dict

class RetrievalMetrics:
    """
    Calcule les métriques de récupération (retrieval) pour évaluer les stratégies RAG.
    Métriques : Recall@5, MRR, nDCG@5, Coverage, Latency
    """
    
    @staticmethod
    def _dedupe_preserve_order(items: List[str]) -> List[str]:
        seen: set[str] = set()
        output: List[str] = []
        for item in items:
            normalized = str(item).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            output.append(normalized)
        return output

    @staticmethod
    def recall_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5) -> float:
        """
        Recall@K : proportion de documents pertinents retrouvés dans le top-K
        
        Args:
            retrieved_ids: IDs des documents récupérés (ordonnés par pertinence)
            relevant_ids: IDs des documents pertinents (gold standard)
            k: nombre de résultats considérés (par défaut 5)
        
        Returns:
            Recall@K entre 0 et 1
        """
        if not relevant_ids:
            return 0.0
        
        unique_retrieved = RetrievalMetrics._dedupe_preserve_order(retrieved_ids)
        top_k_retrieved = set(unique_retrieved[:k])
        relevant_set = set(relevant_ids)
        matches = len(top_k_retrieved & relevant_set)
        
        return matches / len(relevant_set)

    @staticmethod
    def precision_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5) -> float:
        """
        Precision@K : proportion des éléments pertinents dans le top-K retourné.

        Returns:
            Precision@K entre 0 et 1
        """
        if k <= 0:
            return 0.0

        unique_retrieved = RetrievalMetrics._dedupe_preserve_order(retrieved_ids)
        top_k_retrieved = unique_retrieved[:k]
        relevant_set = set(relevant_ids)
        if not top_k_retrieved:
            return 0.0
        matches = sum(1 for r in top_k_retrieved if r in relevant_set)
        return matches / len(top_k_retrieved)
    
    @staticmethod
    def mrr(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
        """
        MRR (Mean Reciprocal Rank) : position moyenne du PREMIER document pertinent
        
        Args:
            retrieved_ids: IDs des documents récupérés (ordonnés)
            relevant_ids: IDs des documents pertinents
        
        Returns:
            MRR entre 0 et 1 (1 = pertinent au rang 1)
        """
        unique_retrieved = RetrievalMetrics._dedupe_preserve_order(retrieved_ids)
        relevant_set = set(relevant_ids)
        
        for rank, doc_id in enumerate(unique_retrieved, start=1):
            if doc_id in relevant_set:
                return 1.0 / rank
        
        return 0.0
    
    @staticmethod
    def ndcg_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5) -> float:
        """
        nDCG@K (Normalized Discounted Cumulative Gain)
        Mesure la qualité du classement en pénalisant les résultats non pertinents en bas de liste
        
        Args:
            retrieved_ids: IDs des documents récupérés
            relevant_ids: IDs des documents pertinents
            k: nombre de résultats considérés
        
        Returns:
            nDCG@K entre 0 et 1
        """
        unique_retrieved = RetrievalMetrics._dedupe_preserve_order(retrieved_ids)
        relevant_set = set(relevant_ids)
        top_k = unique_retrieved[:k]
        
        # DCG : somme pondérée par position
        dcg = 0.0
        for rank, doc_id in enumerate(top_k, start=1):
            relevance = 1.0 if doc_id in relevant_set else 0.0
            dcg += relevance / np.log2(rank + 1)
        
        # Idéal DCG : si tous les top-K étaient pertinents
        ideal_length = min(len(relevant_ids), k)
        idcg = sum(1.0 / np.log2(rank + 1) for rank in range(1, ideal_length + 1))
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def coverage(
        retrieved_ids: List[str],
        all_concepts: List[str],
        resource_token_map: Dict[str, List[str]] | None = None,
        embeddings=None,
        embedding_similarity_threshold: float = 0.75,
    ) -> float:
        """
        Coverage : fraction des concepts clés couverts par les ressources récupérées.
        Utilise matching de tokens avec fallback embedding-based pour meilleure couverture sémantique.
        
        Args:
            retrieved_ids: IDs des documents récupérés
            all_concepts: Tous les concepts importants du domaine
            resource_token_map: tokens descriptifs par ressource, dérivés du corpus (chunks+keywords)
            embeddings: (optional) embedding model pour fallback matching
            embedding_similarity_threshold: seuil cosine pour fallback (défaut 0.75)
        
        Returns:
            Coverage entre 0 et 1
        """
        if not all_concepts:
            return 0.0
        
        concept_tokens: set[str] = set()
        for concept in all_concepts:
            normalized = str(concept).lower()
            normalized = re.sub(r"[àâä]", "a", normalized)
            normalized = re.sub(r"[éèêë]", "e", normalized)
            normalized = re.sub(r"[îï]", "i", normalized)
            normalized = re.sub(r"[ôö]", "o", normalized)
            normalized = re.sub(r"[ûü]", "u", normalized)
            tokens_found = re.findall(r"[a-z0-9]{2,}", normalized)
            concept_tokens.update(tokens_found)

        if not concept_tokens:
            return 0.0

        retrieved_tokens: set[str] = set()
        for doc_id in RetrievalMetrics._dedupe_preserve_order(retrieved_ids):
            if resource_token_map and doc_id in resource_token_map:
                retrieved_tokens.update(resource_token_map[doc_id])
            else:
                retrieved_tokens.update(re.findall(r"[a-z0-9]{2,}", str(doc_id).lower()))

        matches = len(concept_tokens & retrieved_tokens)
        
        if embeddings and matches < len(concept_tokens):
            try:
                for doc_id in RetrievalMetrics._dedupe_preserve_order(retrieved_ids):
                    doc_tokens = resource_token_map.get(doc_id, []) if resource_token_map else []
                    if not doc_tokens:
                        doc_tokens = [str(doc_id)]
                    doc_text = " ".join(doc_tokens)
                    doc_emb = np.array(embeddings.embed_query(doc_text))
                    for concept in all_concepts:
                        concept_emb = np.array(embeddings.embed_query(concept))
                        similarity = np.dot(concept_emb, doc_emb) / (np.linalg.norm(concept_emb) * np.linalg.norm(doc_emb) + 1e-8)
                        if similarity >= embedding_similarity_threshold:
                            normalized_concept = str(concept).lower()
                            tokens_concept = re.findall(r"[a-z0-9]{2,}", normalized_concept)
                            for token in tokens_concept:
                                if token not in concept_tokens:
                                    matches += 1
                                    concept_tokens.add(token)
            except Exception:
                pass
        
        return min(1.0, matches / len(concept_tokens) if concept_tokens else 0.0)
    
    @staticmethod
    def evaluate_single_query(
        retrieved_ids: List[str],
        relevant_ids: List[str],
        all_concepts: List[str],
        latency_ms: float
        , resource_token_map: Dict[str, List[str]] | None = None
    ) -> Dict[str, float]:
        """
        Évalue une seule requête sur toutes les métriques
        
        Args:
            retrieved_ids: Documents récupérés
            relevant_ids: Documents pertinents
            all_concepts: Concepts du domaine
            latency_ms: Temps d'exécution en ms
        
        Returns:
            Dict avec toutes les métriques
        """
        return {
            "recall_at_5": RetrievalMetrics.recall_at_k(retrieved_ids, relevant_ids, k=5),
            "precision_at_5": RetrievalMetrics.precision_at_k(retrieved_ids, relevant_ids, k=5),
            "mrr": RetrievalMetrics.mrr(retrieved_ids, relevant_ids),
            "ndcg_at_5": RetrievalMetrics.ndcg_at_k(retrieved_ids, relevant_ids, k=5),
            "coverage": RetrievalMetrics.coverage(retrieved_ids, all_concepts, resource_token_map=resource_token_map),
            "latency_ms": latency_ms
        }
    
    @staticmethod
    def aggregate_results(all_metrics: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Agrège les résultats de plusieurs requêtes (moyenne)
        
        Args:
            all_metrics: Liste des métriques par requête
        
        Returns:
            Moyennes par métrique
        """
        if not all_metrics:
            return {}
        
        aggregated = {}
        for key in all_metrics[0].keys():
            values = [m[key] for m in all_metrics]
            aggregated[f"{key}_mean"] = np.mean(values)
            aggregated[f"{key}_std"] = np.std(values)
        
        return aggregated


if __name__ == "__main__":
    # Test simple
    retrieved = ["doc1", "doc2", "doc5", "doc10"]
    relevant = ["doc1", "doc2", "doc3"]
    concepts = ["concept_a", "concept_b", "concept_c"]
    
    metrics = RetrievalMetrics.evaluate_single_query(retrieved, relevant, concepts, latency_ms=150.5)
    print("Résultats test :")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
