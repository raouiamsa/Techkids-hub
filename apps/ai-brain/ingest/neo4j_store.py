from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Iterable, Any

from neo4j import GraphDatabase
from langchain_huggingface import HuggingFaceEmbeddings

# =========================
# CONFIGURATION
# =========================
VECTOR_INDEX_NAME = "chunk_embeddings"

# Stopwords étendus (Anglais, Français et Arabe/Tunisien)
STOPWORDS = {
    "a","an","and","are","as","at","be","by","de","des","du",
    "en","et","for","from","has","have","in","is","it","la",
    "le","les","of","on","or","que","qui","sa","se","the",
    "to","un","une","with","dans","pour","sur","par","pas",
    "comment","qu","quoi","quel","quelle","quels","quelles",
    "في","من","على","إلى","و","هو","هي","كان","هذا","هذه","إلي"
}

def normalize_token(value: str) -> str:
    """Nettoyage des tokens : mise en minuscule et suppression des caractères spéciaux."""
    return re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", value.lower()).strip()

def extract_keywords(text: str, limit: int = 20):
    """Extrait des mots-clés uniques pour l'indexation du graphe."""
    tokens = re.findall(r"[A-Za-zÀ-ÿ0-9\u0600-\u06FF']+", text.lower())
    seen, out = set(), []

    for t in tokens:
        t = normalize_token(t)
        if len(t) < 3 or t in STOPWORDS or t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= limit:
            break
    return out


def weighted_reciprocal_rank_fusion(
    ranked_lists: Iterable[tuple[str, Iterable[dict[str, Any]]]],
    *,
    weights: dict[str, float] | None = None,
    k: int = 60,
    top_n: int = 5,
):
    """Fusionne plusieurs classements via RRF pondéré."""
    weights = weights or {}
    scores: dict[str, float] = {}
    best_rows: dict[str, dict[str, Any]] = {}

    for source_name, rows in ranked_lists:
        source_weight = weights.get(source_name, 1.0)

        for rank, row in enumerate(rows, start=1):
            resource_id = str(row.get("resource_id") or "")
            if not resource_id:
                continue

            scores[resource_id] = scores.get(resource_id, 0.0) + source_weight / (k + rank)

            existing_row = best_rows.get(resource_id)
            if existing_row is None or float(row.get("score") or 0.0) > float(existing_row.get("score") or 0.0):
                best_rows[resource_id] = dict(row)

    ordered_resource_ids = sorted(
        scores,
        key=lambda resource_id: (
            -scores[resource_id],
            str(best_rows[resource_id].get("title") or ""),
            resource_id,
        ),
    )

    fused_rows = []
    for resource_id in ordered_resource_ids[:top_n]:
        row = dict(best_rows[resource_id])
        row["score"] = scores[resource_id]
        fused_rows.append(row)

    return fused_rows

# =========================
# CŒUR DU STORE NEO4J
# =========================
class Neo4jStore:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password123")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

        # Utilisation de multilingual-e5-small (384 dimensions)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-small",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self._ensure_schema()

    def _resolve_candidate_ks(self, limit: int, total_candidate_budget: int | None,
                              vector_candidate_k: int | None, graph_candidate_k: int | None):
        """Détermine les tailles des pools de candidats pour vector/graph.

        - `limit` : nombre final d'items retournés.
        - `total_candidate_budget` : taille totale du pool de candidats (si None => limit * 3).
        - `vector_candidate_k`, `graph_candidate_k` : valeurs explicites (peuvent être None).

        Retourne `(vector_k, graph_k, total)` garantissant `vector_k + graph_k <= total`.
        Si la somme dépasse `total`, les valeurs sont normalisées proportionnellement.
        """
        total = int(total_candidate_budget) if total_candidate_budget is not None else max(1, limit * 3)

        if vector_candidate_k is None and graph_candidate_k is None:
            vector_k = total // 2
            graph_k = total - vector_k
        elif vector_candidate_k is None:
            graph_k = max(1, int(graph_candidate_k))
            vector_k = max(1, total - graph_k)
        elif graph_candidate_k is None:
            vector_k = max(1, int(vector_candidate_k))
            graph_k = max(1, total - vector_k)
        else:
            vector_k = max(1, int(vector_candidate_k))
            graph_k = max(1, int(graph_candidate_k))

        # Normaliser si la somme dépasse le budget total
        if vector_k + graph_k > total:
            ratio = total / (vector_k + graph_k)
            vector_k = max(1, int(vector_k * ratio))
            graph_k = max(1, total - vector_k)

        return vector_k, graph_k, total

    def _ensure_schema(self):
        """Initialise les contraintes et l'index vectoriel dans Neo4j."""
        with self.driver.session(database=self.database) as session:
            # Contraintes d'unicité
            session.run("CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.resource_id IS UNIQUE")
            session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE")
            session.run("CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE")

            # Index Vectoriel (384 dims pour E5-small)
            session.run(f"""
            CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {{
              indexConfig: {{
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
              }}
            }}
            """)

    # --- INDEXATION (INGESTION) ---
    def index_documents(self, *, resource_id: str, source_type: str, 
                        title: str, domain: str | None, 
                        source_path_or_url: str, documents: Iterable[Any]):
        """Indexe les documents dans Neo4j avec vecteurs et relations conceptuelles."""
        with self.driver.session(database=self.database) as session:
            # Upsert du nœud Source (Document parent)
            session.run("""
                MERGE (s:Source {resource_id:$id})
                SET s.title=$title, s.type=$type, s.domain=$domain, s.path=$path
            """, id=resource_id, title=title, type=source_type, domain=domain, path=source_path_or_url)

            # Traitement des Chunks (segments de texte)
            for i, doc in enumerate(documents):
                content = getattr(doc, "page_content", "").strip()
                if not content: continue

                metadata = getattr(doc, "metadata", {})
                chunk_id = metadata.get("doc_id") or f"{resource_id}::{i:04d}"
                
                keywords = extract_keywords(content)
                embedding = self.embeddings.embed_query(content)

                session.run("""
                    MATCH (s:Source {resource_id:$rid})
                    MERGE (c:Chunk {chunk_id:$cid})
                    SET c.content=$content, c.embedding=$embedding
                    MERGE (s)-[:HAS_CHUNK]->(c)
                    WITH c
                    UNWIND $keywords AS kw
                    MERGE (k:Concept {name:kw})
                    MERGE (c)-[:MENTIONS]->(k)
                """, rid=resource_id, cid=chunk_id, content=content, embedding=embedding, keywords=keywords)

    # --- MÉTHODES DE RECHERCHE ---

    def _search_vector_candidates(self, embedding: list[float], limit: int):
        query = f"""
        MATCH (c:Chunk)
        SEARCH c IN (
            VECTOR INDEX {VECTOR_INDEX_NAME}
            FOR $embedding
            LIMIT $limit
        ) SCORE AS score
        MATCH (s:Source)-[:HAS_CHUNK]->(c)
        RETURN s.resource_id AS resource_id, s.title AS title, c.content AS content, score
        ORDER BY score DESC
        """
        with self.driver.session(database=self.database) as session:
            res = session.run(query, embedding=embedding, limit=limit)
            return [r.data() for r in res]

    def _search_graph_candidates(self, concepts: Iterable[str], limit: int):
        normalized = [normalize_token(c) for c in concepts if normalize_token(c)]
        query = """
        MATCH (k:Concept)
        WHERE k.name IN $concepts
        MATCH (k)<-[:MENTIONS]-(c:Chunk)<-[:HAS_CHUNK]-(s:Source)
        WITH s, c, count(DISTINCT k) AS score
        RETURN s.resource_id AS resource_id, s.title AS title, c.content AS content, score
        ORDER BY score DESC
        LIMIT $limit
        """
        with self.driver.session(database=self.database) as session:
            res = session.run(query, concepts=normalized, limit=limit)
            return [r.data() for r in res]

    def search_vector_only(self, question: str, limit: int = 5):
        """Recherche vectorielle pure (Similarity Search).

        Parameters exposed for budget control (kept simple here):
        - `limit`: nombre final d'items retournés.
        - `total_candidate_budget` (optional keyword-only): taille totale des candidats.
        - `vector_candidate_k` (optional keyword-only): taille explicite du pool vectoriel.

        Examples:
        `search_vector_only(q, limit=5, total_candidate_budget=30)`
        """
        return self.search_vector_only_with_budget(question, limit=limit)

    def search_vector_only_with_budget(self, question: str, *, limit: int = 5,
                                       total_candidate_budget: int | None = None,
                                       vector_candidate_k: int | None = None):
        emb = self.embeddings.embed_query(question)
        vector_k, _, _ = self._resolve_candidate_ks(limit, total_candidate_budget, vector_candidate_k, None)
        results = self._search_vector_candidates(emb, vector_k)
        return results[:limit]

    def search_graph_only(self, concepts: Iterable[str], limit: int = 5):
        """Recherche par mots-clés dans le graphe (Concept Matching).

        Parameters exposed for budget control:
        - `limit`: nombre final d'items retournés.
        - `total_candidate_budget` (optional keyword-only): taille totale des candidats.
        - `graph_candidate_k` (optional keyword-only): taille explicite du pool graphe.

        Examples:
        `search_graph_only(concepts, limit=5, total_candidate_budget=30)`
        """
        return self.search_graph_only_with_budget(concepts, limit=limit)

    def search_graph_only_with_budget(self, concepts: Iterable[str], *, limit: int = 5,
                                      total_candidate_budget: int | None = None,
                                      graph_candidate_k: int | None = None):
        graph_k = None
        _, graph_k, _ = self._resolve_candidate_ks(limit, total_candidate_budget, None, graph_candidate_k)
        results = self._search_graph_candidates(concepts, graph_k)
        return results[:limit]

    def search_hybrid(
        self,
        question: str,
        concepts: Iterable[str],
        limit: int = 5,
        *,
        total_candidate_budget: int | None = None,
        vector_candidate_k: int | None = None,
        graph_candidate_k: int | None = None,
        rrf_k: int = 60,
        weights: dict[str, float] | None = None,
    ):
        """Recherche hybride via RRF pondéré entre les classements vecteur et graphe.

        Parameters:
        - `limit`: nombre final d'items retournés.
        - `total_candidate_budget`: taille totale du pool de candidats partagé entre les modes.
          Si `None` la valeur par défaut est `limit * 3`.
        - `vector_candidate_k`, `graph_candidate_k`: valeurs optionnelles explicites pour chaque mode.
          Si les deux sont `None`, le budget total est réparti 50/50.
        - `rrf_k`: paramètre 'k' de la formule RRF (reciprocal rank fusion).
        - `weights`: dict des poids par source, p.ex. {"vector":0.45, "graph":0.55}.

        Retourne la liste des `limit` meilleurs résultats après fusion RRF.
        """
        emb = self.embeddings.embed_query(question)
        normalized = [normalize_token(c) for c in concepts if normalize_token(c)]

        vector_k, graph_k, total = self._resolve_candidate_ks(
            limit, total_candidate_budget, vector_candidate_k, graph_candidate_k
        )

        vector_results = self._search_vector_candidates(emb, vector_k)
        graph_results = self._search_graph_candidates(normalized, graph_k)

        final_weights = weights or {"vector": 0.45, "graph": 0.55}

        return weighted_reciprocal_rank_fusion(
            [
                ("vector", vector_results),
                ("graph", graph_results),
            ],
            weights=final_weights,
            k=rrf_k,
            top_n=limit,
        )

@lru_cache(maxsize=1)
def get_neo4j_store():
    return Neo4jStore()


class Neo4jHybridRetriever:
    """Wrapper for Neo4jStore hybrid search (COMP1 strategy for COMP2-5)."""
    
    def __init__(
        self,
        *,
        top_k: int,
        total_candidate_budget: int | None = None,
        vector_candidate_k: int | None = None,
        graph_candidate_k: int | None = None,
        rrf_k: int,
        weights: dict[str, float],
        reranker: str = "lexical",
    ):
        self.store = get_neo4j_store()
        self.top_k = top_k
        self.total_candidate_budget = total_candidate_budget
        self.vector_candidate_k = vector_candidate_k
        self.graph_candidate_k = graph_candidate_k
        self.rrf_k = rrf_k
        self.weights = weights
        self.reranker = reranker

    def search_hybrid(self, query: str, limit: int = 5, concepts: list = None):
        """Search hybrid and return formatted documents for prompt injection."""
        if concepts is None:
            concepts = []
        
        rows = self.store.search_hybrid(
            question=query,
            concepts=concepts,
            limit=limit,
            total_candidate_budget=self.total_candidate_budget,
            vector_candidate_k=self.vector_candidate_k,
            graph_candidate_k=self.graph_candidate_k,
            rrf_k=self.rrf_k,
            weights=self.weights,
        )
        
        # Format results for injection into prompts
        docs = []
        for row in rows[:limit]:
            doc = {
                "resource_id": row.get("resource_id"),
                "title": row.get("title", ""),
                "content": row.get("content", ""),
                "source": row.get("source", ""),
            }
            docs.append(doc)
        
        return docs

    def retrieve(self, question: str, _question_id: int, test_data: dict):
        """Compatibility wrapper matching COMP1 retriever API.

        Returns (list_of_resource_ids, latency_ms)
        """
        import time

        start = time.perf_counter()
        concepts = test_data.get("concepts", []) if isinstance(test_data, dict) else []

        # Reuse search_hybrid to avoid duplicating search logic
        docs = self.search_hybrid(query=question, limit=self.top_k, concepts=concepts)

        latency = (time.perf_counter() - start) * 1000
        ids = [d.get("resource_id") for d in docs if d.get("resource_id")]
        return ids, latency