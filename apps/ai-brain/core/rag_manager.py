import os
from langchain_chroma import Chroma
from langchain_core.documents import Document

# On importe les variables partagées définies dans l'ingestion
from ingest.shared import EMBEDDINGS, CHROMA_PERSIST_DIR

class RAGManager:
    """
    Gestionnaire centralisé pour l'indexation (Event-Driven) et la recherche RAG 
    sur les cours publiés pour les enfants.
    """
    def __init__(self, collection_name="published_courses"):
        self.collection_name = collection_name
        
        # On s'assure que le dossier existe
        if not os.path.exists(CHROMA_PERSIST_DIR):
            os.makedirs(CHROMA_PERSIST_DIR)

        # Initialisation de la connexion à ChromaDB
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=EMBEDDINGS,
            persist_directory=CHROMA_PERSIST_DIR
        )

    def index_course(self, course_id: str, content: str, title: str = "Untitled"):
        """
        Indexe un cours publié dans la base vectorielle.
        Appelé par l'API quand le prof approuve le cours.
        """
        doc = Document(
            page_content=content,
            metadata={"course_id": course_id, "title": title, "type": "approved_course"}
        )
        
        # Ajout au Vector Store
        self.vector_store.add_documents([doc])
        print(f"[RAG] Cours {course_id} ('{title}') indexé avec succès dans {self.collection_name}.")
        return True

    def search_context(self, query: str, top_k: int = 2) -> str:
        """
        Recherche sémantique pour trouver le contexte le plus pertinent.
        Utilisé par le Tuteur Socratique.
        """
        results = self.vector_store.similarity_search(query, k=top_k)
        
        if not results:
            return ""
            
        # Fusionner les extraits trouvés
        context_parts = []
        for i, doc in enumerate(results):
            context_parts.append(f"--- Extrait {i+1} (Source: {doc.metadata.get('title', 'Cours')}) ---\n{doc.page_content}")
            
        return "\n\n".join(context_parts)
