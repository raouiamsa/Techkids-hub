# COMP 2 et COMP 4 : Méthodologie d’évaluation des modèles de langage et de fine-tuning

## 1. Résumé exécutif

Le présent document formalise la méthodologie retenue pour COMP 2, consacré à la comparaison des modèles de langage, et COMP 4, dédié à l’évaluation du fine-tuning. L’approche adoptée repose sur une inférence locale via Ollama pour les mesures de référence, et sur une infrastructure de calcul cloud (Google Colab) pour l’entraînement. Cette organisation hybride permet de garantir la reproductibilité des expérimentations tout en maîtrisant les contraintes matérielles du poste de travail local.

---

## 2. Contexte et motivation

La sélection d’un modèle génératif adapté aux usages pédagogiques constitue une étape déterminante dans la conception du système TechKids Hub. COMP 2 vise à établir des bases de comparaison quantitatives entre trois modèles candidats, à savoir Phi-3, Mistral et Llama, dans leur état pré-entraîné. Les évaluations sont réalisées dans des conditions identiques, à partir du même contexte de récupération issu de la configuration gagnante de COMP 1. COMP 4 examine ensuite l’effet d’un fine-tuning spécialisé sur un corpus pédagogique, afin de mesurer les gains réellement attribuables à l’adaptation au domaine.

### 2.1 Problématique

Les modèles de langage pré-entraînés présentent des performances contrastées selon plusieurs dimensions : qualité sémantique, fidélité au contexte, taux d’hallucination, latence d’inférence et consommation mémoire. Une évaluation expérimentale rigoureuse est donc nécessaire pour orienter les choix d’architecture, de fine-tuning et de déploiement.

### 2.2 Périmètre

- **COMP 2** : génération zero-shot sur un ensemble de questions-réponses pédagogiques.
- **COMP 4** : fine-tuning supervisé sur un corpus éducatif spécialisé, suivi d’une réévaluation comparative.

### 2.3 Justification méthodologique de COMP 2

COMP 2 constitue l’étape de référence de l’étude, car il permet d’établir une **baseline pré-entraînement** pour chaque modèle candidat. Cette baseline est indispensable pour répondre à deux questions distinctes : d’une part, identifier le meilleur modèle avant adaptation ; d’autre part, mesurer de manière rigoureuse l’impact réel du fine-tuning dans COMP 4.

Sans COMP 2, il serait impossible de distinguer la performance intrinsèque d’un modèle de l’amélioration apportée par l’adaptation au domaine. La comparaison initiale ne constitue donc pas une redondance, mais une condition expérimentale nécessaire pour calculer les gains après fine-tuning et justifier scientifiquement le choix du modèle retenu.
**Résumé oral pour défense** : COMP 2 établit la baseline pré-tuning de chaque modèle. COMP 4 mesure le gain du fine-tuning spécialisé. Sans COMP 2, impossible de distinguer la qualité intrinsèque du modèle de l'effet du fine-tuning — c'est méthodologiquement nécessaire pour valider scientifiquement l'amélioration.
---

## 3. Architecture expérimentale

### 3.1 Principe de conception modulaire

Le dispositif d’évaluation repose sur trois composantes faiblement couplées :

```text
┌─────────────────────────────────────────────────────────────────┐
│                   Chaîne d’évaluation COMP 2 et COMP 4          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  Récupération        │  │  Inférence   │  │  Calcul des │  │
│  │  d’information       │──│  locale      │──│  métriques  │  │
│  │  (Neo4j hybride)     │  │  (Ollama)    │  │  (BLEU,     │  │
│  │                      │  │              │  │  ROUGE-L,   │  │
│  │  5 documents        │  │  Réponse     │  │  BERTScore) │  │
│  │  classés par requête │  │  générée     │  │             │  │
│  └──────────────────────┘  └──────────────┘  └─────────────┘  │
│                                                                 │
│  Environnement d’exécution : poste local Windows + WSL2         │
│  GPU : NVIDIA GeForce MX350, usage de modèles quantifiés        │
│  Volume de test : 20 à 30 instances par modèle                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Configuration de récupération fixée par COMP 1

Toutes les évaluations de modèles sont conduites sous une même configuration de récupération afin d’assurer l’équité expérimentale. La stratégie retenue est dérivée du meilleur paramétrage identifié en COMP 1 (`strategy_final.json`) :

```json
{
  "retrieval": {
    "backend": "hybrid",
    "limit": 5,
    "reranker": "lexical",
    "weights": {
      "vector": 0.6,
      "graph": 0.4
    },
    "rrf_k": 60
  }
}
```

**Justification** : la récupération hybride, fondée sur un compromis de 60 % pour la similarité vectorielle et 40 % pour la correspondance par graphe conceptuel, fournit un contexte stable et reproductible. Le réordonnancement lexical renforce la précision des passages retenus. L’usage du Reciprocal Rank Fusion (RRF, k=60) permet une fusion cohérente des scores. Chaque modèle reçoit exactement les mêmes cinq documents de contexte par requête ; la comparaison porte donc exclusivement sur la qualité générative.

---

## 4. COMP 2 : évaluation des modèles de langage en configuration de base

### 4.1 Modèles candidats

Trois modèles pré-entraînés sont retenus comme bases de comparaison :

| Modèle | Organisation | Variante | Ordre de grandeur | Quantification |
|-------|--------------|----------|-------------------|----------------|
| **Phi-3** | Microsoft | 7B | ~3 à 4 milliards de paramètres actifs | GGUF 4 bits |
| **Mistral** | Mistral AI | 7B Instruct | ~7 milliards de paramètres | GGUF 4 bits |
| **Llama** | Meta | 7B | ~7 milliards de paramètres | GGUF 4 bits |

Tous les modèles sont exécutés localement au moyen d’Ollama, sous forme quantifiée, afin de garantir une inférence compatible avec les contraintes de mémoire disponibles. La quantification en 4 bits est appliquée de manière uniforme afin de maintenir un cadre de comparaison cohérent.

### 4.2 Chaîne d’inférence

Pour chaque requête, la séquence suivante est appliquée :

1. **Récupération du contexte** : la question est transmise au récupérateur hybride Neo4j, qui retourne cinq documents classés.
2. **Construction du prompt** : les documents sont formatés en contexte structuré selon un gabarit unique.

   ```text
   Contexte :
   {documents_formattés}

   Question : {question}
   Réponse :
   ```

3. **Génération** : le modèle produit une réponse via l’API locale d’Ollama (`localhost:11434`), avec une génération déterministe et une limite de 256 jetons.
4. **Calcul des métriques** : la réponse obtenue est comparée à la référence au moyen de plusieurs indicateurs complémentaires.

### 4.2.1 Contrainte de sortie structurée

En complément de la qualité sémantique, COMP 2 évalue la capacité des modèles à produire des objets **JSON strictement valides**. Cette contrainte reflète directement le besoin applicatif du projet TechKids Hub, dans lequel les réponses du modèle doivent être consommées par une interface de rendu et transformées en composants pédagogiques.

Le prompt impose donc un schéma fixe et exige que la réponse soit constituée exclusivement d’un objet JSON, sans texte narratif, sans balisage Markdown et sans contenu périphérique.

Schéma représentatif :

```json
{
  "title": "Introduction aux listes",
  "level": "beginner",
  "summary": "...",
  "concepts": [
    {"name": "mutable", "definition": "..."}
  ],
  "examples": [
    {
      "language": "python",
      "code": "fruits = [\"apple\", \"banana\"]"
    }
  ],
  "quiz": [
    {
      "question": "Une liste est-elle modifiable ?",
      "answer": "Oui"
    }
  ]
}
```

Cette contrainte permet une exploitation directe par la couche de présentation et rend la sortie du modèle mesurable sur trois plans : validité du schéma, complétude structurelle et exploitabilité front-end.

### 4.2.2 Structure JSON recommandée pour le rendu frontend

Afin de permettre un rendu modulaire et visuellement riche côté interface, la sortie JSON doit être découpée en blocs fonctionnels indépendants. Chaque bloc correspond à un composant frontend clairement identifié : carte conceptuelle, bloc de code, encadré d’attention, quiz interactif ou illustration.

Structure cible recommandée :

```json
{
  "metadata": {
    "title": "Introduction aux listes",
    "level": "beginner",
    "domain": "python",
    "estimated_duration": "10 min",
    "tags": ["structures de données", "débutant"]
  },
  "learning_objectives": [
    "Comprendre la notion de liste",
    "Identifier les opérations de base sur une liste"
  ],
  "summary": {
    "short": "Une liste est une structure ordonnée et modifiable.",
    "long": "..."
  },
  "concept_cards": [
    {
      "id": "concept-1",
      "title": "Mutable",
      "description": "Une liste peut être modifiée après sa création.",
      "icon": "list"
    }
  ],
  "code_examples": [
    {
      "language": "python",
      "title": "Créer une liste",
      "code": "fruits = [\"apple\", \"banana\"]",
      "explanation": "Cette instruction crée une liste contenant deux éléments.",
      "output_expected": "['apple', 'banana']"
    }
  ],
  "visual_aids": [
    {
      "type": "diagram",
      "title": "Structure d’une liste",
      "description": "Représentation visuelle des éléments et de leur ordre."
    }
  ],
  "quiz": [
    {
      "id": "quiz-1",
      "question": "Une liste est-elle modifiable ?",
      "answer": "Oui",
      "choices": ["Oui", "Non"],
      "difficulty": "easy",
      "explanation": "Une liste Python est mutable: on peut ajouter, supprimer ou modifier des éléments après sa création."
    }
  ],
  "warnings": [
    {
      "type": "attention",
      "message": "Les indices de liste commencent à 0 en Python."
    }
  ],
  "call_to_action": {
    "label": "Essayer un exercice",
    "action": "start_exercise"
  }
}
```

Cette organisation présente plusieurs avantages :

- elle sépare clairement les métadonnées pédagogiques du contenu de présentation ;
- elle permet de générer automatiquement des composants frontend distincts à partir de chaque section ;
- elle favorise un rendu non linéaire, donc plus dynamique et moins monotone ;
- elle facilite la validation du schéma, puisque chaque champ peut être contrôlé de manière indépendante.

En pratique, l’interface peut mapper les champs JSON de la manière suivante :

- `metadata` vers l’en-tête de la fiche de cours ;
- `learning_objectives` vers un bloc d’objectifs ;
- `summary` vers une carte de synthèse ;
- `concept_cards` vers des cartes interactives ;
- `code_examples` vers des blocs de code avec coloration syntaxique ;
- `visual_aids` vers des espaces d’illustration ou de schématisation ;
- `quiz` vers un composant d’évaluation interactive ;
- `warnings` vers des encadrés d’attention ;
- `call_to_action` vers un bouton ou un bloc d’engagement pédagogique.

### 4.3 Indicateurs d’évaluation

COMP 2 ne se limite pas à un score global unique. L’évaluation est organisée en **trois couches complémentaires** afin de localiser précisément la source d’un échec:

1. **Couche RAG**: qualité du contexte récupéré.
2. **Couche LLM**: comportement brut du modèle de génération.
3. **Couche Agent**: succès de la tâche selon le rôle (Architect, Writer, Enricher, Critic).

Cette séparation permet d’interpréter un bon ou mauvais résultat sans ambiguïté: un modèle peut être bon en JSON mais faible en connaissance, ou bon en retrieval mais faible en génération.

#### 4.3.0 Couche RAG

La couche RAG évalue si le contexte transmis au modèle est pertinent et exploitable.

Métriques principales:

- `retrieval_latency_ms`
- `retrieved_docs_count`
- `context_coverage_pct`
- `ragas_context_precision`
- `ragas_context_recall`
- `ragas_faithfulness`
- `ragas_answer_relevancy`

Interprétation:

- une forte précision de contexte indique que les documents récupérés sont pertinents;
- un bon recall indique que les informations importantes ne sont pas perdues;
- la faithfulness mesure si la réponse reste ancrée dans le contexte récupéré.

#### 4.3.1 Couche LLM

La couche LLM mesure le comportement brut du modèle, indépendamment du rôle applicatif.

Métriques principales:

- `llm_latency_ms`
- `ttft_ms`
- `instruction_adherence_pct`
- `format_strictness_pct`
- `hallucination_rate_pct`

Interprétation:

- un bon score ici signifie que le modèle suit les consignes, produit rapidement et limite les écarts factuels;
- un mauvais score avec une bonne récupération signale souvent un problème de modèle ou de prompt.

#### 4.3.2 Couche Agent

La couche Agent mesure si le rôle a accompli sa mission métier.

Chaque agent possède ses propres métriques spécifiques:

- Architect: structure du syllabus, progression pédagogique, complétude des modules.
- Writer: qualité du texte, longueur, lisibilité, richesse éducative, RAGAS.
- Enricher: qualité des QCM, validité des options, cohérence des réponses.
- Critic: cohérence de l’audit, plage du score, richesse des issues.

Le score de l’agent est donc un score de succès de tâche, pas un benchmark générique du modèle.

#### 4.3.3 Pourquoi garder un score en plus des metrics

Les metrics décrivent les causes. Le score donne une synthèse exploitable pour la comparaison finale.

Structure recommandée:

- `RAG Score` = agrégation pondérée des métriques de récupération
- `LLM Score` = agrégation pondérée des métriques de comportement du modèle
- `Agent Score` = agrégation pondérée des métriques spécifiques au rôle
- `Final Score` = combinaison de ces trois scores pour la décision finale

#### 4.3.1 Similarité sémantique et lexicale

- **BLEU**
  - Mesure le recouvrement en n-grammes entre la sortie générée et la réponse de référence.
  - Intervalle : [0, 1], où 1 correspond à une équivalence lexicale maximale.
  - Intérêt : utile pour la précision textuelle, mais sensible aux paraphrases.
  - Implémentation : `nltk.translate.bleu_score` avec lissage de type `method1`.

- **ROUGE-L**
  - Mesure la plus longue sous-séquence commune entre référence et génération.
  - Intervalle : [0, 1].
  - Intérêt : capture plus efficacement la couverture conceptuelle que BLEU.
  - Implémentation : bibliothèque `rouge_score`.

- **BERTScore**
  - Mesure la similarité contextuelle au moyen d’embeddings sémantiques.
  - Intervalle : [0, 1].
  - Intérêt : plus robuste aux reformulations lexicales.
  - Implémentation : bibliothèque `bert_score`.

#### 4.3.2 Factualité et ancrage contextuel

- **Taux d’hallucination**
  - Quantifie la part de contenu non ancrée dans le contexte fourni, c’est-à-dire la **faithfulness** vis-à-vis des documents récupérés depuis Neo4j.
  - Formule simplifiée : `1 - (tokens_communs / tokens_totaux)`.
  - Intervalle : [0, 1], où 0 correspond à l’absence d’hallucination.
  - Les tokens de référence doivent être comparés prioritairement au **contexte issu de la récupération** et non à la seule réponse de référence.

- **Précision de citation**
  - Mesure la proportion de documents sources explicitement mentionnés dans la réponse.
  - Intervalle : [0, 1].
  - Intérêt : particulièrement pertinent pour un usage pédagogique où la traçabilité du contenu est essentielle.

#### 4.3.3 Qualité de la sortie structurée

- **Taux de validité JSON**
  - Mesure la proportion de sorties qui se parsèment correctement en JSON sans correction manuelle.
  - Intervalle : [0, 1].
  - Importance : une réponse non valide ne peut pas être exploitée par l’interface.

- **Adhérence au schéma**
  - Mesure le respect des clés obligatoires, des types attendus et de la structure hiérarchique définie.
  - Intervalle : [0, 1].

- **Score de complétude**
  - Mesure la présence de tous les champs pédagogiquement requis, tels que le titre, le résumé, les concepts, les exemples et le quiz.
  - Intervalle : [0, 1].

#### 4.3.4 Performance et efficacité mémoire

- **Latence**
  - Temps d’inférence global mesuré en millisecondes.
  - Comprend l’encodage du prompt, la génération et le décodage de la réponse.

- **Consommation mémoire**
  - Mesure du pic de mémoire résidentielle (RSS) en mégaoctets.
  - Permet d’évaluer la compatibilité du modèle avec l’environnement local.

### 4.4 Jeu de données

L’évaluation est réalisée sur un ensemble de 20 à 30 questions issues de `sprint4_comp1_testcases.json`. Les exemples couvrent plusieurs domaines pédagogiques, notamment Python, les structures de données et les algorithmes, avec différents niveaux de difficulté. Chaque entrée contient la question, la réponse de référence, les documents pertinents, le domaine et le niveau de difficulté.

### 4.5 Format de sortie et agrégation

Les résultats détaillés sont enregistrés dans un fichier CSV selon le format suivant :

```text
question_id, model, question, reference_answer, generated_answer,
retrieval_latency_ms, retrieved_docs_count, context_coverage_pct,
ragas_context_precision, ragas_context_recall,
ttft_ms, llm_latency_ms, instruction_adherence_pct, hallucination_rate_pct,
json_validity, schema_adherence, completeness_score, latency_ms, memory_mb
```

Les statistiques agrégées sont ensuite calculées par modèle (moyenne, écart-type, minimum et maximum) :

```text
Modèle    | BLEU | ROUGE-L | BERTScore | Hallucination | Préc. citation | JSON valide | Schéma | Complétude | Latence (ms) | Mémoire (MB)
----------|------|---------|-----------|---------------|----------------|-------------|--------|------------|--------------|-------------
Phi-3     | 0.68 | 0.74    | 0.82      | 0.08          | 0.92           | 0.98        | 0.95   | 0.94       | 125          | 2048
Mistral   | 0.65 | 0.71    | 0.80      | 0.12          | 0.88           | 0.93        | 0.90   | 0.91       | 150          | 2200
Llama     | 0.62 | 0.68    | 0.78      | 0.15          | 0.85           | 0.91        | 0.88   | 0.89       | 180          | 2400
```

### 4.6 Critère de sélection du modèle gagnant

Le score composite est défini comme suit :

**Score composite** = `0.2 * RAG Score + 0.3 * LLM Score + 0.5 * Agent Score`

Justification :
- Le RAG Score permet de savoir si le contexte était bon.
- Le LLM Score permet de savoir si le modèle a bien généré.
- Le Agent Score permet de savoir si le rôle a réussi sa tâche.
- Cette séparation évite de confondre un problème de retrieval avec un problème de génération.

---

## 5. COMP 4 : fine-tuning et adaptation supervisée

### 5.1 Objectif

Le fine-tuning vise à adapter le modèle sélectionné en COMP 2 aux spécificités du domaine pédagogique TechKids Hub. L’hypothèse de travail est qu’un entraînement supervisé sur un corpus spécialisé permet d’améliorer à la fois la cohérence du ton, la pertinence des réponses et la robustesse du format JSON attendu.

### 5.2 Infrastructure d’entraînement

**Plateforme** : Google Colaboratory, avec accès GPU (T4 ou A100 selon disponibilité).

**Justification** :
- Colab fournit un environnement prêt à l’emploi pour l’entraînement de modèles ouverts.
- Cette solution évite les contraintes locales liées à CUDA, aux pilotes et à la mémoire GPU limitée.
- Elle facilite la reproductibilité grâce à un environnement versionné et contrôlé.

### 5.2.1 Contrainte matérielle locale

Le poste local utilisé pour l’inférence dispose d’une **NVIDIA GeForce MX350**, qui reste un GPU d’entrée de gamme avec une mémoire vidéo limitée. Cette contrainte matérielle justifie le recours à une inférence locale via **Ollama** avec des modèles **quantifiés en 4 bits**, ainsi qu’à un basculement vers le **CPU inference** lorsque la charge mémoire dépasse la capacité disponible.

Ce choix ne constitue pas une limite méthodologique, mais un compromis technique raisonné : la quantification et l’inférence locale légère permettent de conserver un protocole expérimental stable, reproductible et compatible avec le matériel disponible.

### 5.3 Méthode de fine-tuning

#### 5.3.1 Préparation des données

Le corpus d’entraînement est constitué d’exemples d’instructions pédagogiques, de questions-réponses et de contenus structurés. Le format cible est le suivant :

```json
{
  "instruction": "Expliquer ce qu’est une liste Python.",
  "input": "",
  "output": "Une liste Python est une structure ordonnée et modifiable..."
}
```

La répartition recommandée est de 80 % pour l’entraînement et 20 % pour la validation.

#### 5.3.2 Configuration d’apprentissage

Le fine-tuning est réalisé avec la pile **Hugging Face `transformers` + `peft`**, en utilisant la méthode **LoRA**.

Paramètres indicatifs :
- Taux d’apprentissage : `2e-4`
- Taille de batch : `8`
- Nombre d’époques : `3`
- Rang LoRA : `8`
- Alpha LoRA : `16`
- Warmup steps : `100`
- Longueur maximale de séquence : `512`

L’approche LoRA a été retenue car elle réduit significativement les coûts mémoire tout en conservant de bonnes performances d’adaptation.
Ces hyperparamètres seront ajustés selon les résultats de validation afin de préserver un équilibre entre stabilité, capacité d’adaptation et coût d’entraînement.

#### 5.3.3 Gestion des checkpoints

- Les checkpoints sont sauvegardés à intervalles réguliers.
- Le meilleur modèle est sélectionné sur la base de la perte de validation.
- Le modèle final est exporté dans deux formats :
  - format PyTorch pour une utilisation avec `transformers` ;
  - format GGUF pour une exécution locale via Ollama.

### 5.4 Réévaluation post fine-tuning

Le modèle fine-tuné est réévalué sur le même jeu de test que COMP 2, avec les mêmes prompts et les mêmes métriques. L’analyse compare :

1. la performance absolue du modèle avant et après fine-tuning ;
2. les gains relatifs en RAG Score, LLM Score, Agent Score et métriques spécifiques par agent ;
3. la significativité statistique des écarts observés au moyen de tests appariés.

### 5.5 Résultats attendus

- Fichier CSV détaillé par requête.
- Synthèse agrégée des performances.
- Analyse des gains après adaptation.
- Export du modèle final pour usage local.

---

## 6. Reproductibilité et validation

### 6.1 Chaîne logicielle

**Évaluation locale (COMP 2)** :
- Python 3.10 ou supérieur.
- Ollama pour l’inférence locale.
- Neo4j pour la récupération hybride.
- Bibliothèques de métriques : `nltk`, `rouge_score`, `bert_score`, `psutil`.

**Entraînement distant (COMP 4)** :
- Google Colab.
- `transformers`, `peft`, `torch`.
- Export vers Hugging Face Hub ou stockage Colab.

### 6.2 Mesures de reproductibilité

1. Fixation des graines aléatoires.
2. Versionnement strict des dépendances.
3. Sérialisation des paramètres d’expérience.
4. Conservation du jeu de données de test.
5. Archivage des journaux d’exécution et des résultats.

### 6.3 Liste de validation

- Le contexte de récupération est identique pour tous les modèles.
- Le gabarit de prompt reste constant.
- Les métriques sont indépendantes du modèle évalué.
- Les graines aléatoires sont fixées.
- Les données d’entraînement et de validation sont séparées.
- Le jeu de test demeure distinct du corpus de fine-tuning.

---

## 7. Résultats attendus et critères de succès

### 7.1 COMP 2

- Obtention de scores comparables par modèle.
- Identification des modes d’échec propres à chaque architecture.
- Sélection d’un modèle gagnant selon le score composite et les contraintes matérielles.

### 7.2 COMP 4

- Amélioration mesurable des indicateurs de qualité après fine-tuning.
- Réduction du taux d’hallucination.
- Meilleure conformité à la sortie JSON attendue.

Critère de succès indicatif : amélioration d’au moins 10 % sur un sous-ensemble des métriques principales, ou gain statistiquement significatif à `p < 0.05`.

---

## 8. Calendrier et allocation des ressources

| Phase | Durée estimée | Ressources | Livrable |
|-------|---------------|------------|----------|
| Préparation COMP 2 | 2 à 3 h | Poste local | Baselines et modèle retenu |
| Fine-tuning COMP 4 | 4 à 6 h | Google Colab GPU | Checkpoint adapté au domaine |
| Réévaluation post-entraînement | 1 à 2 h | Poste local | Comparaison avant/après |
| Rédaction et synthèse | 2 à 3 h | Poste local | Rapport final |

---

## 9. Hypothèses et limites

### 9.1 Hypothèses

1. La récupération hybride fournit un contexte suffisamment représentatif.
2. Les réponses de référence constituent un standard acceptable pour la comparaison.
3. Les métriques retenues capturent correctement les dimensions principales de la qualité générative.
4. Le corpus de fine-tuning reflète de manière cohérente le domaine pédagogique visé.

### 9.2 Limites

1. La taille réduite du jeu de test limite la puissance statistique.
2. Les heuristiques de hallucination et de citation restent approximatives.
3. La quantification peut induire une légère dégradation des performances absolues.
4. La disponibilité GPU sur Colab n’est pas garantie de manière permanente.

---

## 10. Conclusion

Cette méthodologie établit un cadre expérimental rigoureux pour comparer des modèles de langage et mesurer l’effet d’un fine-tuning spécialisé. L’utilisation d’Ollama pour l’inférence locale, de Neo4j pour la récupération et de Google Colab pour l’entraînement permet de concilier reproductibilité, efficacité et faisabilité matérielle. Les résultats obtenus orienteront directement les choix de modélisation, de déploiement et d’intégration du système TechKids Hub.

---

## Annexe : commandes de référence

### Exécution de COMP 2

```bash
# Activation de l’environnement virtuel
.venv\Scripts\activate

# Lancement d’un test COMP 2 (exemple Phi-3)
python apps/ai-brain/benchmarking/comp2_llm_baseline_runner.py \
    --model_path phi-3-mini-gguf \
    --model_name phi-3 \
    --device cpu \
    --test_limit 20
```

### Fine-tuning COMP 4 sur Colab

```python
%pip install -q transformers peft torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import get_peft_model, LoraConfig

# ... boucle d'entraînement ...
model.save_pretrained("/content/model_out")
```

---

**Version du document** : 1.1  
**Date** : 9 mai 2026  
**Statut** : version académique prête pour intégration au rapport
