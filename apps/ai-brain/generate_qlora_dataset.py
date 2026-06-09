import os
import json
import time
import requests

# ==========================================
# CONFIGURATION
# ==========================================
# Remplace par ta vraie clé Google Gemini API
GEMINI_API_KEY = "AIzaSyBV6gUFpfN-hnepWEXeXNKYrtBVi0cF3D4" 

# On utilise Gemini 3.1 Flash Lite car il t'offre 15 RPM et 500 RPD !
MODEL_NAME = "gemini-3.1-flash-lite"

OUTPUT_FILE = "dataset_qlora.jsonl"

# Liste des sujets pour générer le dataset
TOPICS = [
    # Programmation Visuelle (Scratch / Débutants)
    "Faire avancer un lutin dans Scratch",
    "Créer un score dans un jeu Scratch",
    "Les conditions si/sinon dans Scratch",
    "Les boucles répéter dans Scratch",
    "Détecter une collision dans Scratch",
    "Dessiner avec le stylo dans Scratch",
    "Créer des clones dans Scratch",
    "Ajouter du son à un jeu Scratch",
    "Créer un jeu de Pong dans Scratch",
    "Utiliser les variables dans Scratch",

    # Programmation Textuelle (Python)
    "Les variables en Python",
    "La boucle for en Python",
    "La boucle while en Python",
    "Les conditions if/else en Python",
    "Les fonctions en Python",
    "Les listes en Python",
    "Les dictionnaires en Python",
    "Gérer les erreurs (try/except) en Python",
    "Lire et écrire dans un fichier en Python",
    "Créer une interface graphique avec Tkinter",
    "Créer un jeu simple avec Pygame",
    "Comprendre les modules et bibliothèques en Python",
    "Manipuler des chaînes de caractères en Python",
    "La programmation orientée objet (Classes) en Python",
    "Faire des calculs mathématiques avec Python",

    # Électronique & IoT (Arduino / Circuits)
    "Qu'est-ce qu'un circuit électrique fermé ?",
    "La différence entre le courant continu et alternatif",
    "Allumer une LED avec Arduino",
    "Lire un bouton poussoir avec Arduino",
    "Le capteur à ultrasons (HC-SR04) avec Arduino",
    "Le capteur de température (DHT11) avec Arduino",
    "Contrôler un moteur Servo avec Arduino",
    "Utiliser une photorésistance (LDR) avec Arduino",
    "Faire du bruit avec un Buzzer sur Arduino",
    "Afficher du texte sur un écran LCD avec Arduino",
    "Utiliser un potentiomètre avec Arduino",
    "Connecter Arduino au Wi-Fi (ESP8266)",
    "Créer un feu de circulation avec Arduino",
    "Piloter un moteur à courant continu avec Arduino",
    "Qu'est-ce qu'une résistance et comment la calculer ?",

    # Culture Tech & Ingénierie
    "L'intelligence artificielle expliquée simplement",
    "Comment fonctionne Internet ?",
    "Le binaire : comment comptent les ordinateurs ?",
    "Qu'est-ce qu'un algorithme ?",
    "Les bases de la cybersécurité et des mots de passe",
    "Comment fonctionne un réseau Wi-Fi ?",
    "Qu'est-ce que le Cloud Computing ?",
    "Comprendre le fonctionnement d'un processeur (CPU)",
    "La différence entre la RAM et le disque dur",
    "Comment fonctionnent les capteurs de nos smartphones ?"
]

# ==========================================
# FONCTION API GEMINI
# ==========================================
def call_gemini(system_prompt, user_prompt, require_json=True):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": user_prompt}]}
        ]
    }
    
    # Force Gemini à répondre uniquement en JSON
    if require_json:
        data["generationConfig"] = {
            "responseMimeType": "application/json"
        }
        
    for attempt in range(5):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            print(f"   ⏳ Limite Gemini atteinte (Essai {attempt+1}/5). Pause de 15 secondes...")
            time.sleep(15)
        else:
            print(f"   ❌ Erreur API ({response.status_code}): {response.text}")
            time.sleep(5)
            
    return None

# ==========================================
# PROMPTS DES AGENTS (CORRIGÉS POUR COMP2_JSON_SCHEMA)
# ==========================================
def get_architect_prompt():
    return """Tu es l'Architecte Pédagogique. Ton but est de créer la structure du cours pour un enfant de 12 ans.
Tu dois générer un JSON valide respectant cette structure exacte :
{
  "metadata": {
    "title": "Titre engageant",
    "level": "beginner",
    "domain": "computer_science",
    "age_group": "11-13",
    "estimated_duration": "15 mins",
    "tags": ["motcle1", "motcle2"]
  },
  "learning_objectives": ["Objectif concret 1", "Objectif concret 2"],
  "summary": {
    "short": "Résumé en une phrase pour attirer l'attention.",
    "long": "Résumé plus détaillé en trois phrases expliquant ce que l'enfant va apprendre."
  }
}"""

def get_writer_prompt():
    return """Tu es le Rédacteur Pédagogique. Ton but est d'écrire le cours pour un enfant de 12 ans avec un ton très chaleureux, encourageant et très simple (LIX < 35).
Tu dois générer un JSON valide respectant cette structure exacte :
{
  "concept_cards": [
    {
      "id": "concept-1",
      "title": "Nom du concept",
      "description": "Explication hyper simple",
      "icon": "💡"
    }
  ],
  "content": {
    "sections": [
      {
        "id": "section-1",
        "title": "Titre de la section",
        "subtitle": "Sous-titre engageant",
        "icon": "📖",
        "preview": "Teasing d'une phrase de ce qu'on va voir.",
        "content": "Le texte explicatif complet, chaleureux et adapté aux 12 ans.",
        "difficulty": "easy",
        "estimated_read_time": "5 min",
        "has_visual": false,
        "has_code": false,
        "has_question": false
      }
    ]
  }
}"""

def get_enricher_prompt():
    return """Tu es l'Enrichisseur Pédagogique. Ton but est d'ajouter du code, des visuels et des exercices.
Tu dois générer un JSON valide respectant cette structure exacte :
{
  "code_examples": [
    {
      "language": "python",
      "title": "Titre du code",
      "code": "print('hello')",
      "explanation": "Explication de ce que fait le code",
      "output_expected": "hello"
    }
  ],
  "visual_aids": [
    {
      "type": "illustration",
      "title": "Titre de l'image",
      "description": "Description visuelle détaillée",
      "url_or_placeholder": "placeholder_image.png"
    }
  ],
  "quiz": [
    {
      "id": "quiz-1",
      "question": "Question ?",
      "answer": "La bonne réponse exacte",
      "choices": ["Option A", "La bonne réponse exacte"],
      "difficulty": "easy",
      "explanation": "Parce que..."
    }
  ],
  "exercises": [
    {
      "id": "exercise-1",
      "type": "code",
      "title": "Titre de l'exercice",
      "instructions": "Consignes de l'exercice",
      "difficulty": "easy",
      "estimated_time": "5 min"
    }
  ],
  "warnings": [
    {
      "type": "attention",
      "message": "Faites attention à..."
    }
  ],
  "call_to_action": {
    "label": "Passer à la suite",
    "action": "next_module"
  }
}"""

# ==========================================
# GÉNÉRATION DU DATASET Llama 3 Instruct Format
# ==========================================
def format_llama3_interaction(system, user, assistant):
    return (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n{assistant}<|eot_id|>"
    )

def main():
    print(f"🚀 Lancement de la génération du dataset avec {MODEL_NAME}")
    
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for topic in TOPICS:
            print(f"\n--- Traitement du sujet : {topic} ---")
            
            # ÉTAPE 0 : Mock RAG
            print("1. Génération du contexte RAG (Mock)...")
            mock_rag_prompt = "Tu es un expert en technologie. Donne moi 3 paragraphes d'informations techniques et précises sur: " + topic
            context = call_gemini("Tu es une encyclopédie STEM.", mock_rag_prompt, require_json=False)
            
            if not context: continue
            
            # ÉTAPE 1 : Architect
            print("2. Génération Architect...")
            sys_arch = get_architect_prompt()
            user_arch = f"Sujet : {topic}\nContexte RAG : {context}"
            out_arch = call_gemini(sys_arch, user_arch)
            
            if out_arch:
                f.write(json.dumps({"text": format_llama3_interaction(sys_arch, user_arch, out_arch)}) + "\n")
                
            # ÉTAPE 2 : Writer
            print("3. Génération Writer...")
            sys_write = get_writer_prompt()
            user_write = f"Plan de l'architecte : {out_arch}\nContexte RAG : {context}"
            out_write = call_gemini(sys_write, user_write)
            
            if out_write:
                f.write(json.dumps({"text": format_llama3_interaction(sys_write, user_write, out_write)}) + "\n")
                
            # ÉTAPE 3 : Enricher
            print("4. Génération Enricher...")
            sys_enrich = get_enricher_prompt()
            user_enrich = f"Contenu du rédacteur : {out_write}\nContexte RAG : {context}"
            out_enrich = call_gemini(sys_enrich, user_enrich)
            
            if out_enrich:
                f.write(json.dumps({"text": format_llama3_interaction(sys_enrich, user_enrich, out_enrich)}) + "\n")

            print("⏳ Sujet terminé. Pause de 15 secondes pour respecter le quota Gemini (15 RPM)...")
            time.sleep(15)
            
    print(f"\n✅ Terminé ! Dataset généré avec succès dans {OUTPUT_FILE}")

if __name__ == "__main__":
    main()