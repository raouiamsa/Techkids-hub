import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Dict, List

AI_BRAIN_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(AI_BRAIN_DIR))

from ingest.neo4j_store import get_neo4j_store, normalize_token
from ingest.shared import CHROMA_PERSIST_DIR, EMBEDDINGS
from langchain_chroma import Chroma
from metrics.llm.retrieval_metrics import RetrievalMetrics

DATASET_PATH = AI_BRAIN_DIR / "benchmarking/dataset/sprint4_comp1_testcases.json"
RESOURCE_MANIFEST_PATH = AI_BRAIN_DIR / "benchmarking/dataset/sprint4_comp1_resources.json"
OUTPUT_DIR = AI_BRAIN_DIR / "benchmarking/outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INGEST_MANIFEST_PATH = AI_BRAIN_DIR / "data" / "ingest_manifest.json"

# Fixed COMP1 defaults for current embedding experiment.
DEFAULT_EMBEDDING_TAG = "intfloat/multilingual-e5-small"
DEFAULT_CHUNK_SIZE = "1200"
DEFAULT_CHUNK_OVERLAP = "200"
DEFAULT_TOP_KS = [3, 5, 8]
DEFAULT_RERANKER_OPTIONS = ["lexical"]


def _parse_csv_ints(value: str, default: List[int]) -> List[int]:
    if not value:
        return default
    out: List[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out or default


def _parse_csv_options(value: str, default: List[str]) -> List[str]:
    if not value:
        return default
    out = [x.strip().lower() for x in value.split(",") if x.strip()]
    return out or default


def _to_output_tag(value: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip())
    return sanitized.strip("_") or "embedding"


def _build_run_tag(embedding_tag: str, chunk_size: str, chunk_overlap: str) -> str:
    embedding_part = _to_output_tag(embedding_tag)
    chunk_size_part = _to_output_tag(f"cs{chunk_size}")
    chunk_overlap_part = _to_output_tag(f"co{chunk_overlap}")
    return f"{embedding_part}_{chunk_size_part}_{chunk_overlap_part}"


def load_ingest_manifest_config() -> dict:
    if not INGEST_MANIFEST_PATH.exists():
        return {}
    try:
        payload = json.loads(INGEST_MANIFEST_PATH.read_text(encoding="utf-8"))
        return payload.get("config", {}) if isinstance(payload, dict) else {}
    except Exception:
        return {}


def load_testcases() -> List[dict]:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_resources() -> List[dict]:
    with open(RESOURCE_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _tokenize_text(text: str) -> List[str]:
    """Tokenize text with accent normalization for coverage computation."""
    normalized = text.lower()
    normalized = re.sub(r"[àâä]", "a", normalized)
    normalized = re.sub(r"[éèêë]", "e", normalized)
    normalized = re.sub(r"[îï]", "i", normalized)
    normalized = re.sub(r"[ôö]", "o", normalized)
    normalized = re.sub(r"[ûü]", "u", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return [token for token in normalized.split() if len(token) >= 2]


def build_token_map(resources: List[Dict]) -> Dict[str, List[str]]:
    """Build token map from resource metadata (title/domain) - fallback only."""
    token_map: Dict[str, List[str]] = {}
    for r in resources:
        rid = str(r.get("resource_id") or "")
        text = f"{r.get('title', '')} {r.get('domain', '')}"
        tokens = list(set(re.findall(r"[a-z0-9]{3,}", text.lower())))
        token_map[rid] = tokens
    return token_map


def build_token_map_from_neo4j(store) -> dict:
    """Build token map from Neo4j chunk contents (primary source for coverage)."""
    token_map = {}
    query = """
    MATCH (s:Source)-[:HAS_CHUNK]->(c:Chunk)
    RETURN s.resource_id AS resource_id, s.title AS title, s.domain AS domain, c.content AS content
    ORDER BY s.resource_id
    """
    try:
        with store.driver.session(database=store.database) as session:
            for record in session.run(query):
                resource_id = str(record.get("resource_id") or "")
                if not resource_id:
                    continue
                content = str(record.get("content") or "")
                title = str(record.get("title") or "")
                domain = str(record.get("domain") or "")
                tokens = []
                for text in (title, domain, content):
                    tokens.extend(_tokenize_text(text))
                token_map[resource_id] = list(dict.fromkeys(tokens))[:500]
    except Exception as e:
        print(f"Warning: Neo4j chunk token map failed: {e}, using fallback.")
        return {}
    return token_map


def rerank_with_token_overlap(question: str, retrieved_ids: List[str], token_map: Dict[str, List[str]], top_k: int) -> List[str]:
    q_tokens = set(re.findall(r"[a-z0-9]{3,}", question.lower()))
    if not q_tokens:
        return retrieved_ids[:top_k]

    scored = []
    for rank, rid in enumerate(retrieved_ids):
        r_tokens = set(token_map.get(str(rid), []))
        overlap = len(q_tokens & r_tokens)
        # tie-breaker keeps original order stable
        scored.append((overlap, -rank, rid))

    scored.sort(reverse=True)
    return [rid for _, _, rid in scored][:top_k]


def dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


class ChromaDBRetriever:
    def __init__(self, top_k: int):
        self.vectorstore = Chroma(persist_directory=str(CHROMA_PERSIST_DIR), embedding_function=EMBEDDINGS)
        self.store = get_neo4j_store()  # For access to embeddings
        self.top_k = top_k
        self.total_candidate_budget = top_k * 3
        self.vector_candidate_k = top_k * 3
        self.graph_candidate_k = 0
        self.rrf_k = None
        self.weights = {}
        self.reranker = "off"

    def retrieve(self, question: str, _question_id: int, _test_data: dict):
        start = time.perf_counter()
        docs = self.vectorstore.similarity_search(question, k=self.top_k)
        latency = (time.perf_counter() - start) * 1000

        ids = []
        seen = set()
        for d in docs:
            rid = str(d.metadata.get("course_id") or d.metadata.get("resource_id") or "")
            if rid and rid not in seen:
                seen.add(rid)
                ids.append(rid)
        return ids, latency


class Neo4jVectorRetriever:
    def __init__(self, top_k: int):
        self.store = get_neo4j_store()
        self.top_k = top_k
        self.total_candidate_budget = top_k * 3
        self.vector_candidate_k = top_k * 3
        self.graph_candidate_k = 0
        self.rrf_k = None
        self.weights = {}
        self.reranker = "off"

    def retrieve(self, question: str, _question_id: int, _test_data: dict):
        start = time.perf_counter()
        rows = self.store.search_vector_only(question, limit=self.top_k)
        latency = (time.perf_counter() - start) * 1000
        return [r.get("resource_id") for r in rows if r.get("resource_id")], latency


class Neo4jGraphRetriever:
    def __init__(self, top_k: int):
        self.store = get_neo4j_store()
        self.top_k = top_k
        self.total_candidate_budget = top_k * 3
        self.vector_candidate_k = 0
        self.graph_candidate_k = top_k * 3
        self.rrf_k = None
        self.weights = {}
        self.reranker = "off"

    def retrieve(self, _question: str, _question_id: int, test_data: dict):
        start = time.perf_counter()
        concepts = test_data.get("concepts", [])
        rows = self.store.search_graph_only(concepts=concepts, limit=self.top_k)
        latency = (time.perf_counter() - start) * 1000
        return [r.get("resource_id") for r in rows if r.get("resource_id")], latency


class Neo4jHybridRetriever:
    def __init__(
        self,
        *,
        top_k: int,
        total_candidate_budget: int | None,
        vector_candidate_k: int | None,
        graph_candidate_k: int | None,
        rrf_k: int,
        weights: Dict[str, float],
        reranker: str,
    ):
        self.store = get_neo4j_store()
        self.top_k = top_k
        self.total_candidate_budget = total_candidate_budget
        self.vector_candidate_k = vector_candidate_k
        self.graph_candidate_k = graph_candidate_k
        self.rrf_k = rrf_k
        self.weights = weights
        self.reranker = reranker

    def retrieve(self, question: str, _question_id: int, test_data: dict):
        start = time.perf_counter()
        concepts = test_data.get("concepts", [])
        rows = self.store.search_hybrid(
            question=question,
            concepts=concepts,
            limit=self.top_k,
            total_candidate_budget=self.total_candidate_budget,
            vector_candidate_k=self.vector_candidate_k,
            graph_candidate_k=self.graph_candidate_k,
            rrf_k=self.rrf_k,
            weights=self.weights,
        )
        latency = (time.perf_counter() - start) * 1000
        return [r.get("resource_id") for r in rows if r.get("resource_id")], latency


def _safe_csv_path(path: Path) -> Path:
    if not path.exists():
        return path
    try:
        with open(path, "a", newline="", encoding="utf-8"):
            return path
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return path.with_name(f"{path.stem}_{stamp}{path.suffix}")


def run():
    ingest_cfg = load_ingest_manifest_config()

    embedding_tag = str(ingest_cfg.get("embedding_model") or DEFAULT_EMBEDDING_TAG)
    chunk_size = str(ingest_cfg.get("chunk_size") or DEFAULT_CHUNK_SIZE)
    chunk_overlap = str(ingest_cfg.get("chunk_overlap") or DEFAULT_CHUNK_OVERLAP)
    output_tag = _build_run_tag(embedding_tag, chunk_size, chunk_overlap)

    k_options = DEFAULT_TOP_KS
    reranker_options = DEFAULT_RERANKER_OPTIONS

    total_candidate_budget_options: List[int | None] = [None, 30]
    weights_options = [
        {"vector": 0.45, "graph": 0.55},
        {"vector": 0.5, "graph": 0.5},
        {"vector": 0.6, "graph": 0.4},
    ]
    rrf_k_options = [60, 30]

    output_csv = _safe_csv_path(OUTPUT_DIR / f"comp1_retrieval_ablation_{output_tag}.csv")
    output_summary_csv = _safe_csv_path(OUTPUT_DIR / f"comp1_retrieval_ablation_summary_{output_tag}.csv")

    print("\n==============================")
    print("COMP1 ABLATION BENCHMARK")
    print("==============================")
    print(f"Embedding tag: {embedding_tag}")
    print(f"Chunking tag: size={chunk_size or 'NA'} overlap={chunk_overlap or 'NA'}")
    print(f"Top-k grid: {k_options}")
    print(f"Reranker options: {reranker_options}\n")

    testcases = load_testcases()
    resources = load_resources()
    store = get_neo4j_store()
    
    print("Building coverage token map from Neo4j chunks...")
    token_map = build_token_map_from_neo4j(store)
    if not token_map:
        print("Falling back to resource metadata for token map.")
        token_map = build_token_map(resources)

    strategies: List[tuple[str, object]] = []

    for top_k in k_options:
        strategies.append((f"Chroma (Vector) k={top_k}", ChromaDBRetriever(top_k)))
        strategies.append((f"Neo4j (Vector) k={top_k}", Neo4jVectorRetriever(top_k)))
        strategies.append((f"Neo4j (Graph) k={top_k}", Neo4jGraphRetriever(top_k)))

    for top_k, total_cb, weights, rrf_k, reranker in product(
        k_options,
        total_candidate_budget_options,
        weights_options,
        rrf_k_options,
        reranker_options,
    ):
        name = (
            f"Neo4j (Hybrid) k={top_k} tc={total_cb or 'def'} "
            f"w={int(weights['vector'] * 100)}/{int(weights['graph'] * 100)} "
            f"rrf={rrf_k} reranker={reranker}"
        )
        retriever = Neo4jHybridRetriever(
            top_k=top_k,
            total_candidate_budget=total_cb,
            vector_candidate_k=None,
            graph_candidate_k=None,
            rrf_k=rrf_k,
            weights=weights,
            reranker=reranker,
        )
        strategies.append((name, retriever))

    all_results: List[dict] = []

    for name, retriever in strategies:
        print(f"\n--- {name} ---")
        metrics_list: List[dict] = []

        for tc in testcases:
            qid = tc["question_id"]
            q = tc["question"]
            retrieved, latency = retriever.retrieve(q, qid, tc)
            retrieved = dedupe_keep_order(retrieved)

            if getattr(retriever, "reranker", "lexical") == "lexical":
                retrieved = rerank_with_token_overlap(q, retrieved, token_map, getattr(retriever, "top_k", 5))

            k_eval = int(getattr(retriever, "top_k", 5))
            recall = RetrievalMetrics.recall_at_k(retrieved, tc["relevant_documents"], k=k_eval)
            precision = RetrievalMetrics.precision_at_k(retrieved, tc["relevant_documents"], k=k_eval)
            ndcg = RetrievalMetrics.ndcg_at_k(retrieved, tc["relevant_documents"], k=k_eval)
            mrr = RetrievalMetrics.mrr(retrieved, tc["relevant_documents"])
            # Improved coverage with embedding fallback
            coverage_kwargs = {"resource_token_map": token_map, "embedding_similarity_threshold": 0.70}
            if hasattr(retriever, "store") and retriever.store:
                coverage_kwargs["embeddings"] = retriever.store.embeddings
            coverage = RetrievalMetrics.coverage(retrieved, tc.get("concepts", []), **coverage_kwargs)

            metrics = {
                "question_id": qid,
                "strategy": name,
                "evaluation_k": k_eval,
                "recall_at_k": recall,
                "precision_at_k": precision,
                "mrr": mrr,
                "ndcg_at_k": ndcg,
                "coverage": coverage,
                "latency_ms": latency,
                "total_candidate_budget": getattr(retriever, "total_candidate_budget", None),
                "vector_candidate_k": getattr(retriever, "vector_candidate_k", None),
                "graph_candidate_k": getattr(retriever, "graph_candidate_k", None),
                "rrf_k": getattr(retriever, "rrf_k", None),
                "weights": getattr(retriever, "weights", None),
                "reranker": getattr(retriever, "reranker", "off"),
                "embedding_tag": embedding_tag,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            }

            all_results.append(metrics)
            metrics_list.append(metrics)

        avg_recall = sum(m["recall_at_k"] for m in metrics_list) / len(metrics_list)
        avg_precision = sum(m["precision_at_k"] for m in metrics_list) / len(metrics_list)
        avg_mrr = sum(m["mrr"] for m in metrics_list) / len(metrics_list)
        avg_ndcg = sum(m["ndcg_at_k"] for m in metrics_list) / len(metrics_list)
        avg_coverage = sum(m["coverage"] for m in metrics_list) / len(metrics_list)
        avg_latency = sum(m["latency_ms"] for m in metrics_list) / len(metrics_list)

        print(
            f"✔ Recall@{getattr(retriever, 'top_k', 5)}: {avg_recall:.4f} | "
            f"Precision@{getattr(retriever, 'top_k', 5)}: {avg_precision:.4f} | "
            f"MRR: {avg_mrr:.4f} | nDCG@{getattr(retriever, 'top_k', 5)}: {avg_ndcg:.4f} | "
            f"Coverage: {avg_coverage:.4f}"
        )
        print(f"✔ Latency: {avg_latency:.2f} ms")

        mean_row = {
            "question_id": "MEAN",
            "strategy": name,
            "evaluation_k": getattr(retriever, "top_k", 5),
            "recall_at_k": avg_recall,
            "precision_at_k": avg_precision,
            "mrr": avg_mrr,
            "ndcg_at_k": avg_ndcg,
            "coverage": avg_coverage,
            "latency_ms": avg_latency,
            "total_candidate_budget": getattr(retriever, "total_candidate_budget", None),
            "vector_candidate_k": getattr(retriever, "vector_candidate_k", None),
            "graph_candidate_k": getattr(retriever, "graph_candidate_k", None),
            "rrf_k": getattr(retriever, "rrf_k", None),
            "weights": getattr(retriever, "weights", None),
            "reranker": getattr(retriever, "reranker", "off"),
            "embedding_tag": embedding_tag,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
        all_results.append(mean_row)

    fieldnames = [
        "question_id",
        "strategy",
        "evaluation_k",
        "recall_at_k",
        "precision_at_k",
        "mrr",
        "ndcg_at_k",
        "coverage",
        "latency_ms",
        "total_candidate_budget",
        "vector_candidate_k",
        "graph_candidate_k",
        "rrf_k",
        "weights",
        "reranker",
        "embedding_tag",
        "chunk_size",
        "chunk_overlap",
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    mean_rows = [r for r in all_results if str(r.get("question_id")) == "MEAN"]
    with open(output_summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mean_rows)

    print("\n==============================")
    print(f"DETAILS SAVED → {output_csv}")
    print(f"SUMMARY SAVED → {output_summary_csv}")
    print("==============================")


if __name__ == "__main__":
    run()
