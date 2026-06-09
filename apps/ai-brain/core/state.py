from typing import List, TypedDict, Annotated
import operator

class AgentState(TypedDict):
    """
    Représente l'état partagé entre tous les agents du pipeline LangGraph.
    """
    input_request: str           # La demande initiale du professeur (ex: "Introduction au Python")
    course_ids: List[str]        # Liste des sources (PDF, URLs) sélectionnées
    syllabus: str                # Le plan de cours structuré généré par l'Architecte (JSON string)
    content: Annotated[List[str], operator.add] # Historique cumulatif via reducer
    age_group: int               # Âge des élèves pour l'adaptation pédagogique
    level: str                   # Niveau de difficulté (BEGINNER, INTERMEDIATE, ADVANCED)
    teacher_feedback: str        # Commentaires ou directives de révision fournis par le professeur
    include_code_exercises: bool # Option pour activer la génération d'exercices de programmation
    iterations: int              # Compteur de cycles pour limiter les révisions automatiques
    source_documents: List[dict] # Métadonnées enrichies des sources (citations)(Page PDF, Minutes YouTube, etc.)
    draft_id: str                # Identifiant unique du brouillon pour la communication avec NestJS
    
    # DATA POUR LE FINE-TUNING ET MODE CHIRURGICAL 
    initial_prompt: str          # Le prompt complet (Sujet + Âge + Niveau + Notes) stocké tel quel
    module_feedbacks: dict       #  feedbacks par module {"Titre Module": "Feedback"}

    #  ÉVALUATIONS ET PROJETS
    placement_bank: str          # Questions QCM de diagnostic initial (JSON string)
    certification_bank: str      # Banque de 20 questions pour l'examen final (JSON string)
    final_project: str           # Énoncé, étapes et solution du projet de synthèse (JSON string)
    programming_language: str    # Langage technique détecté ou choisi pour le cours (ex: Python, C++)

    #  DIAGNOSTIC ADAPTATIF (Architectural Intelligence) 
    subject_type: str            # Type du sujet détecté : 'programming'|'math'|'science'|'theory'|'mixed'
    has_code_in_pdf: bool        # True si le PDF source contient du code réel extractible
    pdf_code_strategy: str       # type exercice : 'code_from_pdf'|'code_from_llm'|'calculation'|'qcm_only'

    #  ESTHÉTIQUE ET IDENTITÉ VISUELLE (Phase 4)
    style_conceptuel: str        # Style pour l'IA (ex: "3D Pixar")
    style_technique: str         # Style pour la recherche Web Fritzing (ex: "Schéma plat 2D")
    proposed_images: list        # Liste des images proposées (générées et extraites) en attente de validation
    is_syllabus_approved: bool   # Statut de validation de l'architecte par l'enseignant
    is_content_approved: bool    # Statut de validation du contenu final et des images par l'enseignant

    # ── RECTIFICATION CHIRURGICALE ──
    existing_content: dict       # Contenu existant à préserver lors d'une rectification partielle
    existing_syllabus: str       # Syllabus existant à réutiliser 