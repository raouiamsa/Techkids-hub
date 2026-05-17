from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Dict, Optional

# Import Neo4j retriever (defined in neo4j_store.py)
from ingest.neo4j_store import Neo4jHybridRetriever


@dataclass
class RetrievalStrategy:
    name: str
    backend: str
    limit: int
    reranker: str
    weights: Dict[str, float]
    total_candidate_budget: Optional[int]
    vector_candidate_k: Optional[int]
    graph_candidate_k: Optional[int]
    rrf_k: int
    rerank_top_k: int


@dataclass
class IndexProvenance:
    chunk_size: int
    chunk_overlap: int
    embeddings_model: str


@dataclass
class Strategy:
    name: str
    retrieval: RetrievalStrategy
    index_provenance: IndexProvenance


def get_final_strategy() -> Strategy:
    """Return the canonical comparison baseline from COMP 1 winner.

    Retrieval is fixed for COMP 2-5. Index provenance records the
    chunking used to create the current embeddings index.
    """
    return Strategy(
        name="retrieval_baseline_comp1_to_comp5",
        retrieval=RetrievalStrategy(
            name="hybrid_lexical_winner",
            backend="hybrid",
            limit=5,
            reranker="lexical",
            weights={"vector": 0.6, "graph": 0.4},
            total_candidate_budget=None,
            vector_candidate_k=None,
            graph_candidate_k=None,
            rrf_k=60,
            rerank_top_k=100,
        ),
        index_provenance=IndexProvenance(
            chunk_size=1000,
            chunk_overlap=150,
            embeddings_model="intfloat/multilingual-e5-small",
        ),
    )


def get_retriever_from_strategy(strategy: Strategy) -> Neo4jHybridRetriever:
    """Instantiate a Neo4jHybridRetriever from a Strategy object."""
    retr = strategy.retrieval
    return Neo4jHybridRetriever(
        top_k=retr.limit,
        total_candidate_budget=retr.total_candidate_budget,
        vector_candidate_k=retr.vector_candidate_k,
        graph_candidate_k=retr.graph_candidate_k,
        rrf_k=retr.rrf_k,
        weights=retr.weights,
        reranker=retr.reranker,
    )


def load_strategy_json(path: str | Path) -> Strategy:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    retrieval = payload.get("retrieval", {})
    index_provenance = payload.get("index_provenance", {})
    return Strategy(
        name=str(payload.get("name", "retrieval_baseline_comp1_to_comp5")),
        retrieval=RetrievalStrategy(
            name=str(retrieval.get("name", "hybrid_lexical_baseline")),
            backend=str(retrieval.get("backend", "hybrid")),
            limit=int(retrieval.get("limit", 5)),
            reranker=str(retrieval.get("reranker", "lexical")),
            weights=dict(retrieval.get("weights", {"vector": 0.5, "graph": 0.5})),
            total_candidate_budget=retrieval.get("total_candidate_budget"),
            vector_candidate_k=retrieval.get("vector_candidate_k"),
            graph_candidate_k=retrieval.get("graph_candidate_k"),
            rrf_k=int(retrieval.get("rrf_k", 30)),
            rerank_top_k=int(retrieval.get("rerank_top_k", 100)),
        ),
        index_provenance=IndexProvenance(
            chunk_size=int(index_provenance.get("chunk_size", 1000)),
            chunk_overlap=int(index_provenance.get("chunk_overlap", 150)),
            embeddings_model=str(index_provenance.get("embeddings_model", "intfloat/multilingual-e5-small")),
        ),
    )


def save_strategy_json(path: str | Path) -> None:
    s = get_final_strategy()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(s), f, indent=2, ensure_ascii=False)


def strategy_path() -> Path:
    return Path(__file__).with_name("strategy_final.json")


if __name__ == "__main__":
    save_strategy_json(strategy_path())
    print(f"Wrote {strategy_path().name}")
