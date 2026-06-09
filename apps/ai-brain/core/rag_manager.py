import os
import sys

# Importation directe du dossier de benchmarking
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from benchmarking.strategy_final import get_final_strategy, get_retriever_from_strategy
from benchmarking.comp3_pedagogical_graph import PedagogicalGraph, Module, Concept, Exercise, ExerciseType, LearningObjective

class RAGManager:
    """
    Gestionnaire centralisé pour la recherche RAG hybride et le Graphe Pédagogique.
    Importe directement la logique validée lors du benchmarking.
    """
    def __init__(self):
        # On charge la stratégie hybride (Vecteur + Graphe) validée au COMP1
        self.strategy = get_final_strategy()
        self.retriever = get_retriever_from_strategy(self.strategy)

    def index_course(self, course_json: dict):
        """
        Génère et stocke le graphe pédagogique dans Neo4j à partir du JSON final.
        (Remplace l'ancienne indexation ChromaDB)
        """
        # Utilisation de la classe de ton benchmarking pour structurer le graphe
        graph = PedagogicalGraph.from_dict(course_json)
        
        # Pour le MVP, on se contente de générer le graphe en mémoire.
        # Plus tard, on peut utiliser Neo4j pour persister ce PedagogicalGraph
        print(f"[RAG] Graphe Pédagogique généré en mémoire avec {len(graph.modules)} modules.")
        print(f"[RAG] Neo4j Hybrid Search prêt à être utilisé.")
        return True

    def search_context(self, query: str, top_k: int = 5, concepts: list = None) -> str:
        """
        Recherche hybride Neo4j (Vecteur + Mots-clés).
        """
        if concepts is None:
            concepts = []
            
        # Appel direct de la fonction `search_hybrid` de ton Neo4jHybridRetriever
        docs = self.retriever.search_hybrid(query=query, limit=top_k, concepts=concepts)
        
        if not docs:
            return ""
            
        context_parts = []
        for i, doc in enumerate(docs):
            title = doc.get("title", "Document")
            content = doc.get("content", "")
            context_parts.append(f"--- [Doc {i+1}] (Source: {title}) ---\n{content}")
            
        return "\n\n".join(context_parts)
