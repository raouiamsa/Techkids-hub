import json
import re

DATASET_FILE = "dataset_qlora.jsonl"

# Les schémas partiels attendus pour chaque agent
SCHEMAS_ATTENDUS = {
    "Architecte Pédagogique": {"metadata", "learning_objectives", "summary"},
    "Rédacteur Pédagogique": {"concept_cards", "content"},
    "Enrichisseur Pédagogique": {"code_examples", "visual_aids", "exercises", "quiz", "warnings", "call_to_action"}
}

def extract_assistant_json(text):
    """Extrait le JSON généré par l'assistant dans le template Llama 3"""
    match = re.search(r"<\|start_header_id\|>assistant<\|end_header_id\|>\n\n(.*?)<\|eot_id\|>", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return "JSON_INVALID"
    return None

def detect_agent(text):
    """Détecte l'agent à partir du prompt système"""
    if "Tu es l'Architecte Pédagogique" in text:
        return "Architecte Pédagogique"
    elif "Tu es le Rédacteur Pédagogique" in text:
        return "Rédacteur Pédagogique"
    elif "Tu es l'Enrichisseur Pédagogique" in text:
        return "Enrichisseur Pédagogique"
    return "Inconnu"

def main():
    print("🔍 Début de la validation du dataset QLoRA...\n")
    
    total_lignes = 0
    erreurs = 0

    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        for ligne_num, ligne in enumerate(f, 1):
            total_lignes += 1
            data = json.loads(ligne)
            texte_complet = data.get("text", "")
            
            agent = detect_agent(texte_complet)
            json_genere = extract_assistant_json(texte_complet)

            # 1. Vérification si le JSON est cassé
            if json_genere == "JSON_INVALID":
                print(f"❌ Erreur Ligne {ligne_num} ({agent}) : Le JSON est mal formaté (erreur de syntaxe).")
                erreurs += 1
                continue
            
            if json_genere is None:
                print(f"❌ Erreur Ligne {ligne_num} ({agent}) : Aucun bloc assistant trouvé.")
                erreurs += 1
                continue

            # 2. Vérification des clés exactes de l'agent
            cles_generees = set(json_genere.keys())
            cles_attendues = SCHEMAS_ATTENDUS.get(agent, set())

            if cles_generees != cles_attendues:
                print(f"❌ Erreur Ligne {ligne_num} ({agent}) :")
                print(f"   Clés manquantes : {cles_attendues - cles_generees}")
                print(f"   Clés en trop    : {cles_generees - cles_attendues}")
                erreurs += 1

    print("\n==================================")
    print(f"✅ Validation terminée.")
    print(f"📊 Lignes testées : {total_lignes}")
    if erreurs == 0:
        print("🎉 RÉSULTAT : 100% PARFAIT ! Ton dataset est prêt pour le Fine-Tuning.")
    else:
        print(f"⚠️ RÉSULTAT : {erreurs} erreurs trouvées. Il faudra les corriger.")
    print("==================================")

if __name__ == "__main__":
    main()