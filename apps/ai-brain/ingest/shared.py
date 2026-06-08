import os
import faulthandler
faulthandler.enable()

# Empêcher HF de faire des requêtes réseau (contourne le crash de socket.getaddrinfo sous Windows)
os.environ["HF_HUB_OFFLINE"] = "1"

from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from .ingest_config import AI_BRAIN_DIR, EMBEDDING_MODEL_NAME

load_dotenv()

# ── EMBEDDINGS LOCAUX PARTAGÉS ──
print(f"Archiviste : Chargement du modèle de vecteurs ({EMBEDDING_MODEL_NAME})...")
EMBEDDINGS = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

CHROMA_PERSIST_DIR = str(AI_BRAIN_DIR / "data" / "chroma_db")