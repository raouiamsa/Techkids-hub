from __future__ import annotations

import json
import hashlib
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure ai-brain package imports resolve when running script from repo root
AI_BRAIN_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_BRAIN_DIR))

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma


def _load_runtime_dependencies():
    from ingest.ingest_config import CHUNK_SIZE, CHUNK_OVERLAP, write_ingest_manifest
    return CHUNK_SIZE, CHUNK_OVERLAP, write_ingest_manifest


CHROMA_PERSIST_DIR = str(AI_BRAIN_DIR / "data" / "chroma_db")


class LocalHashEmbedding:
    """Deterministic lightweight embeddings that do not require model downloads."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _tokenize(self, text: str) -> List[str]:
        cleaned = text.lower()
        cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in cleaned)
        return [token for token in cleaned.split() if token]

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        tokens = self._tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest, "big") % self.dimension
            vector[bucket] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm > 0:
            vector = [value / norm for value in vector]
        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


def _build_documents_from_graph(graph_path: Path) -> List[Document]:
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    modules = payload.get("modules", {}) or {}
    concepts = payload.get("concepts", {}) or {}
    exercises = payload.get("exercises", {}) or {}

    docs: List[Document] = []

    # Create a document per module containing module metadata, concept definitions and exercises
    for module in sorted(modules.values(), key=lambda m: (m.get("order_in_curriculum", 0), m.get("id", ""))):
        module_id = module.get("id") or ""
        lines: List[str] = [f"Module: {module.get('name', module.get('title',''))}"]
        lines.append(f"module_id={module_id}")
        lines.append(f"prerequisites={module.get('prerequisites_modules', [])}")

        concept_ids = module.get("concepts", []) or []
        for cid in concept_ids:
            c = concepts.get(cid, {})
            lines.append(f"Concept: {c.get('name', cid)}")
            lines.append(f"Definition: {c.get('definition', '')}")
            lines.append(f"Prerequisites: {c.get('prerequisites', [])}")

        ex_ids = module.get("exercises", []) or []
        for eid in ex_ids:
            e = exercises.get(eid, {})
            lines.append(f"Exercise: {e.get('question', eid)}")
            lines.append(f"Type: {e.get('type', '')} | Answer: {e.get('correct_answer', '')}")

        text = "\n".join(lines)
        docs.append(Document(page_content=text, metadata={"module_id": module_id, "source": str(graph_path.name), "type": "comp3_module"}))

    # Also create a document per concept for finer-grained retrieval
    for cid, c in concepts.items():
        text = "\n".join([
            f"Concept: {c.get('name', cid)}",
            f"Definition: {c.get('definition', '')}",
            f"Prerequisites: {c.get('prerequisites', [])}",
        ])
        docs.append(Document(page_content=text, metadata={"concept_id": cid, "source": str(graph_path.name), "type": "comp3_concept"}))

    return docs


def index_comp3_json(graph_json_path: str | Path) -> bool:
    path = Path(graph_json_path)
    if not path.exists():
        raise FileNotFoundError(f"Graph JSON not found: {path}")

    print(f"Loading runtime dependencies for {path.name}...", flush=True)
    CHUNK_SIZE, CHUNK_OVERLAP, write_ingest_manifest = _load_runtime_dependencies()
    embeddings = LocalHashEmbedding()
    print("Runtime dependencies loaded.", flush=True)

    docs = _build_documents_from_graph(path)
    if not docs:
        return False

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)
    chunks = [c for c in chunks if c.page_content and c.page_content.strip()]

    print(f"Indexing {len(chunks)} chunks into Chroma ({CHROMA_PERSIST_DIR})...", flush=True)

    # Assign stable doc ids
    for i, chunk in enumerate(chunks):
        if "doc_id" not in chunk.metadata:
            chunk.metadata["doc_id"] = f"comp3::{path.stem}::{i:04d}"

    # Persist into Chroma (one-time index)
    try:
        Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_PERSIST_DIR)
        # Write ingest manifest for provenance
        write_ingest_manifest(source_id=path.stem, source_type="comp3_json", source_path_or_url=str(path), success=True)
        print("Indexing completed successfully.", flush=True)
        return True
    except Exception as exc:
        print(f"Indexing failed: {exc}", flush=True)
        try:
            write_ingest_manifest(source_id=path.stem, source_type="comp3_json", source_path_or_url=str(path), success=False)
        except Exception:
            pass
        return False


class ChromaRetrieverWrapper:
    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self._store = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=LocalHashEmbedding())

    def search_hybrid(self, query: str, limit: int = 5, concepts: list | None = None) -> List[Dict[str, Any]]:
        # For Chroma-only retrieval, ignore concepts and do a similarity search
        docs = self._store.similarity_search(query, k=limit)
        out = []
        for d in docs:
            out.append({
                "resource_id": d.metadata.get("course_id") or d.metadata.get("doc_id") or "",
                "title": d.metadata.get("title", ""),
                "content": d.page_content,
                "source": d.metadata.get("source", "chroma"),
            })
        return out


def get_chroma_retriever(top_k: int = 5) -> ChromaRetrieverWrapper:
    return ChromaRetrieverWrapper(top_k=top_k)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Index COMP3 JSON into ChromaDB and provide a retriever wrapper")
    p.add_argument("--index-json", type=str, help="Path to COMP3 graph JSON to index")
    p.add_argument("--top-k", type=int, default=5, help="Top-k for retrieval testing")
    args = p.parse_args()

    if args.index_json:
        print("Starting COMP3 JSON indexing...", flush=True)
        ok = index_comp3_json(args.index_json)
        print(f"Indexing {'succeeded' if ok else 'failed'}", flush=True)
