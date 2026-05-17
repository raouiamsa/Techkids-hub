from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AI_BRAIN_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = AI_BRAIN_DIR / "data"
INGEST_MANIFEST_PATH = DATA_DIR / "ingest_manifest.json"

EMBEDDING_MODEL_NAME = os.getenv("AI_BRAIN_EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
CHUNK_SIZE = int(os.getenv("AI_BRAIN_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("AI_BRAIN_CHUNK_OVERLAP", "150"))


def current_index_config() -> dict[str, Any]:
    return {
        "embedding_model": EMBEDDING_MODEL_NAME,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }


def write_ingest_manifest(*, source_id: str, source_type: str, source_path_or_url: str, success: bool) -> None:
    """Persist the effective ingestion config so benchmarks can read the real indexed setup."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "config": current_index_config(),
        "last_source": {
            "source_id": source_id,
            "source_type": source_type,
            "source_path_or_url": source_path_or_url,
            "success": success,
        },
    }

    if INGEST_MANIFEST_PATH.exists():
        try:
            existing = json.loads(INGEST_MANIFEST_PATH.read_text(encoding="utf-8"))
            history = existing.get("history", [])
            if isinstance(history, list):
                history.append(payload["last_source"] | {"indexed_at": payload["indexed_at"]})
                payload["history"] = history[-100:]
        except Exception:
            pass

    INGEST_MANIFEST_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
