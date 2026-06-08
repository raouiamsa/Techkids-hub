print("TEST 1")
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from ingest.shared import EMBEDDINGS, CHROMA_PERSIST_DIR
    print("TEST 2: ingest.shared imported")
except Exception as e:
    print("TEST 2 FAILED:", e)

try:
    from langchain_chroma import Chroma
    print("TEST 3: langchain_chroma imported")
except Exception as e:
    print("TEST 3 FAILED:", e)

try:
    from ragas_integration.evaluator import LocalRagasEvaluator
    print("TEST 4: ragas_integration imported")
except Exception as e:
    print("TEST 4 FAILED:", e)

print("TEST 5: DONE")
