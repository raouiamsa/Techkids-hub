# Méthodologie de Sélection des Composants IA (COMP 1-5)

## Contexte

Le PFE 4 requiert l'intégration de plusieurs composants critiques : une stratégie de récupération d'information (retrieval), un modèle de génération de texte (LLM), une structure de représentation des connaissances (graphe), et une technique d'adaptation au domaine (fine-tuning). La sélection des composants optimaux sur une architecture matérielle contrainte (GPU MX350, 2GB VRAM) nécessite une méthodologie scientifique rigoureuse.

## Problématique

Une approche brute-force testant toutes les combinaisons possibles conduirait à évaluer 54 configurations (3 stratégies de retrieval × 3 modèles LLM × 3 structures de graphe × 2 états de fine-tuning). Cette approche serait impraticable : elle exigerait approximativement 54 heures de tests, soit bien au-delà des contraintes temporelles du sprint (14 jours).

## Solution proposée : Approche en cascade

Plutôt que de tester toutes les combinaisons, nous proposons une méthodologie en cinq étapes (COMP 1-5) qui isole chaque décision, élimine progressivement les options non viables, et réduit l'espace de recherche à un nombre traitable de configurations finales.

### Principes fondamentaux

1. **Univariance progressive** : Chaque comparaison (COMP 1-4) teste un seul facteur en maintenant les autres constants.
2. **Élimination** : Les options non performantes sont écartées après chaque étape.
3. **Validation finale** : COMP 5 teste les 5 configurations restantes pour détecter les interactions inattendues et valider le choix final.

---

## COMP 1 : Stratégie de Récupération (Jour 3)

### Objectif

Identifier la stratégie de récupération d'information la plus appropriée pour alimenter le pipeline RAG du PFE 4.

### Configurations évaluées

- **ChromaDB seul** : recherche par similarité sémantique via embeddings.
- **Neo4j seul** : requêtes sur graphe de connaissances.
- **Hybrid** : fusion parallèle de ChromaDB et Neo4j.

### Jeu de test

- 30 documents (10 PDF, 10 transcriptions YouTube, 10 articles web).
- 15-20 questions de test avec annotations de pertinence.
- Domaines équilibrés : tech générale, IA, IT, contenu pédagogique.

### Métriques

| Métrique | Description | Seuil |
|----------|-------------|-------|
| Recall@5 | Proportion de documents pertinents trouvés dans le top-5 | > 0.75 |
| MRR | Position moyenne du premier document pertinent | > 0.65 |
| nDCG@5 | Qualité du classement pondérée par pertinence | > 0.70 |
| Coverage | Fraction de concepts pédagogiques clés retrouvés | > 0.80 |
| Latency | Temps moyen de récupération (ms) | < 300ms |

### Résultats attendus

| Métrique | ChromaDB | Neo4j | Hybrid |
|----------|----------|-------|--------|
| Recall@5 | 0.72 | 0.68 | **0.85** |
| MRR | 0.65 | 0.60 | **0.78** |
| Coverage | 0.70 | 0.75 | **0.88** |
| Latency (ms) | 150 | 200 | 250 |

### Décision

La stratégie **Hybrid** est retenue pour son supériorité en couverture conceptuelle (+23% par rapport à ChromaDB) et sa meilleure capacité à équilibrer pertinence sémantique et structurale. Bien que la latence soit plus élevée, elle reste acceptable (250ms < 300ms).

---

## COMP 2 : Modèles de Génération Baseline (Jour 3, parallèle)

### Objectif

Comparer les modèles LLM en baseline (avant fine-tuning) pour identifier le meilleur candidat pour adaptation au domaine pédagogique.

### Modèles évalués

- **Phi-3-mini** : 3.8B paramètres, quantization 4-bit.
- **Mistral 7B** : 7B paramètres, quantization 4-bit.
- **Llama 2 7B** : 7B paramètres, quantization 4-bit.

### Protocole expérimental

Tous les modèles sont testés avec la stratégie Hybrid retenue en COMP 1. Pour chaque question de test, le modèle reçoit les documents récupérés en contexte et génère un cours complet. 50 courses sont générés par modèle.

### Métriques

| Métrique | Description | Seuil |
|----------|-------------|-------|
| BLEU | Similarité lexicale avec réponse de référence | > 0.40 |
| ROUGE-L | Chevauchement d'ordre logique | > 0.50 |
| BERTScore | Similarité sémantique (embeddings) | > 0.65 |
| Hallucination Rate | Proportion d'affirmations non sourçables (%) | < 20% |
| Citation Precision | Proportion d'assertions citant une source (%) | > 85% |
| Latency (ms) | Temps de génération d'un cours (~500 tokens) | < 300ms |
| Memory (GB) | Consommation VRAM en inférence | < 8GB |

### Résultats attendus (Baseline)

| Métrique | Phi-3 | Mistral | Llama2 |
|----------|-------|---------|--------|
| BLEU | 0.42 | **0.48** | 0.45 |
| ROUGE-L | 0.50 | **0.54** | 0.52 |
| BERTScore | 0.68 | **0.72** | 0.70 |
| Hallucination (%) | 0.18 | **0.15** | 0.20 |
| Citation Precision (%) | 0.88 | **0.90** | 0.86 |
| Latency (ms) | **120** | 180 | 200 |
| Memory (GB) | **4.2** | 5.8 | 6.1 |

### Observation

Mistral obtient les meilleurs scores de qualité en baseline. Phi-3 offre un meilleur compromis vitesse-mémoire. Le fine-tuning (COMP 4) déterminera quel modèle s'adapte le mieux au domaine pédagogique.

---

## COMP 3 : Structure de Graphe de Connaissances (Jour 4)

### Objectif

Déterminer quelle structure de graphe optimise la représentation et la récupération de connaissances pédagogiques.

### Structures testées

- **Graphe simple** : Entités (concepts) et relations génériques (mentions, related_to).
- **Graphe pédagogique** : Entités et relations spécialisées (PREREQUISITE_OF, PART_OF, APPLIED_IN, MISCONCEPTION_OF, LEADS_TO).
- **Graphe multimodal** : Concepts, images et vidéos interconnectés par relations sémantiques.

### Protocole expérimental

Chaque structure de graphe est intégrée au pipeline Hybrid + Mistral baseline. Pour chaque question, le système récupère documents et concepts connexes, puis génère un cours. 50 courses par structure.

### Métriques

| Métrique | Description | Seuil |
|----------|-------------|-------|
| Concept Coverage | Fraction de concepts clés retrouvés (%) | > 80% |
| QA Accuracy | Exactitude des réponses factuelles extraites (%) | > 70% |
| Pedagogical Score | Évaluation humaine : clarté, progression, pertinence (1-5) | > 4.0 |
| Latency (ms) | Temps total de récupération et génération | < 300ms |

### Résultats attendus

| Métrique | Simple | Pédagogique | Multimodal |
|----------|--------|-------------|-----------|
| Concept Coverage (%) | 0.70 | **0.88** | 0.85 |
| QA Accuracy (%) | 0.70 | **0.78** | 0.76 |
| Pedagogical Score (1-5) | 3.2 | **4.1** | 3.9 |
| Latency (ms) | 200 | 250 | 300 |

### Décision

Le **graphe pédagogique** est retenu pour sa supériorité en couverture conceptuelle et en correctness pédagogique. Les relations structurées explicitement (PREREQUISITE_OF, etc.) améliorent significativement la qualité de progression des cours générés.

---

## COMP 4 : Fine-tuning QLoRA et comparaison post-adaptation (Jour 4-5, Colab parallèle)

### Objectif

Évaluer les modèles après fine-tuning QLoRA sur les mêmes métriques que celles utilisées en baseline, afin d'identifier le meilleur modèle final pour le déploiement. Le gain relatif sert uniquement à mesurer l'effet de l'adaptation, mais la décision principale repose sur les performances finales obtenues après fine-tuning.

### Modèles fine-tunés

- **Phi-3-mini + QLoRA**
- **Mistral 7B + QLoRA**
- **Llama 2 7B + QLoRA**

### Données d'entraînement

- 300 exemples de (question, contexte_récupéré, cours_idéal).
- Diversifiés sur les domaines de test.
- Validation sur 50 exemples de COMP 2.

### Hyperparamètres (identiques pour tous)

- Rank (r) = 16
- Alpha = 32
- Quantization = 4-bit
- Epochs = 3
- Batch size = 2
- Learning rate = 5e-4

### Exécution

Trois notebooks Colab lancés en parallèle (GPU T4, ~3h par modèle). Export en format GGUF quantized 4-bit après entraînement.

### Métriques de décision

| Métrique | Description |
|----------|-------------|
| BLEU | Similarité lexicale avec la référence |
| ROUGE-L | Chevauchement d'ordre logique |
| BERTScore | Similarité sémantique (embeddings) |
| Hallucination Rate | Proportion d'affirmations non sourçables (%) |
| Citation Precision | Proportion d'assertions citant une source (%) |
| Latency (ms) | Temps d'inférence post-fine-tuning |
| Memory (GB) | Consommation VRAM en inférence |

### Métriques complémentaires

| Métrique | Description |
|----------|-------------|
| BLEU Gain (%) | Amélioration relative de BLEU par rapport à la baseline |
| BERTScore Gain (%) | Amélioration relative de similarité sémantique |
| Hallucination Reduction (%) | Réduction relative du taux d'hallucination |
| Training Time (h) | Durée d'entraînement sur Colab T4 |
| GGUF Size (MB) | Taille du modèle exporté |

### Résultats attendus

| Métrique | Phi-3+LoRA | Mistral+LoRA | Llama2+LoRA |
|----------|-----------|-------------|-----------|
| BLEU (post) | **0.58** | 0.56 | 0.54 |
| BERTScore (post) | **0.79** | 0.77 | 0.75 |
| Hallucination (%) (post) | **0.08** | 0.10 | 0.12 |
| BLEU Gain (%) | **+38%** | +17% | +20% |
| Hallucin Reduction (%) | **-56%** | -33% | -40% |
| Training Time (h) | **2.5** | 3.2 | 3.1 |
| GGUF Size (MB) | **2400** | 4000 | 4100 |
| Latency (ms) (post) | **120** | 180 | 200 |

### Décision

La décision finale doit être prise à partir des **métriques finales post-fine-tuning**, en comparant directement les modèles fine-tunés entre eux. Dans ce cadre, le gain relatif n'est pas le critère principal de sélection, mais un indicateur complémentaire qui permet de mesurer l'intérêt réel du fine-tuning.

**Phi-3-mini + QLoRA** est retenu si ses métriques finales dominent les autres modèles après adaptation. Justifications possibles :
- Meilleure qualité finale sur BLEU, ROUGE-L et BERTScore.
- Taux d'hallucination le plus faible.
- Meilleure précision de citation.
- Latence et consommation mémoire compatibles avec MX350.

Le gain relatif est conservé dans le rapport pour démontrer que le fine-tuning apporte une amélioration mesurable, mais la sélection du modèle final repose d'abord sur la performance absolue après fine-tuning.

---

## COMP 5 : Test d'Intégration Complète (Jour 5)

### Objectif

Valider que la combinaison des meilleures composantes produit un système cohérent et performant. Détecter d'éventuelles interactions négatives ou surcoûts non prévus.

### Configurations finales testées

**Clarification** : dans ce tableau, "Hybrid" désigne la combinaison ChromaDB + Neo4j, et "Pedagogical" désigne le type de graphe utilisé dans Neo4j.

| Config | Retrieval Strategy | LLM | Neo4j Graph Type | Fine-tune | Type |
|--------|-----------|-----|-------|-----------|------|
| A | ChromaDB only | Phi-3 | N/A | ✗ | Baseline |
| B | ChromaDB only | Phi-3 | N/A | ✓ | Impact fine-tune |
| C | Hybrid (ChromaDB + Neo4j Simple) | Phi-3 | Simple | ✗ | Impact retrieval |
| **D** | **Hybrid (ChromaDB + Neo4j Pedagogical)** | **Phi-3** | **Pedagogical** | **✓** | **Théorique optimal** |
| E | Hybrid (ChromaDB + Neo4j Pedagogical) | Mistral | Pedagogical | ✓ | Alternative robuste |

### Protocole

Chaque configuration traite les 15-20 questions de test. Le pipeline complet est exécuté : récupération → génération → évaluation. Mesures identiques pour toutes les configurations.

### Métriques E2E

| Métrique | Description | Seuil |
|----------|-------------|-------|
| QA Accuracy (%) | Exactitude des réponses factuelles | > 85% |
| Hallucination Rate (%) | Taux d'affirmations non sourçables | < 8% |
| Citation Precision (%) | Proportion d'assertions sourçables | > 90% |
| Latency (ms) | Temps complet question → cours | < 300ms |
| Memory Peak (GB) | Pic de mémoire durant génération | < 8GB |
| Pedagogical Score (1-5) | Évaluation expert : clarté, progression, pertinence | > 4.0 |

### Résultats attendus

| Métrique | Config A | Config B | Config C | **Config D** | Config E |
|----------|----------|----------|----------|------------|----------|
| QA Accuracy (%) | 72 | 78 | 82 | **88** | 86 |
| Hallucination (%) | 18 | 8 | 12 | **5** | 6 |
| Citation Precision (%) | 78 | 85 | 90 | **92** | 91 |
| Latency (ms) | 150 | 150 | 250 | **250** | 320 |
| Memory Peak (GB) | 4.2 | 4.2 | 4.2 | **4.2** | 5.8 |
| Pedagogical Score (1-5) | 3.1 | 3.8 | 3.9 | **4.2** | 4.1 |

### Matrice décisionnelle (scoring pondéré)

Poids assignés :
- QA Accuracy : 40% (qualité centrale)
- Hallucination Rate : 25% (fiabilité pédagogique critique)
- Latency : 15% (UX)
- Memory : 10% (contrainte hardware)
- Pedagogical Score : 10% (objectif éducatif)

Scores normalisés (0-1) :

| Dimension | Config A | Config B | Config C | **Config D** | Config E |
|-----------|----------|----------|----------|------------|----------|
| Quality | 0.82 | 0.88 | 0.93 | **1.00** | 0.98 |
| Reliability (Halluc) | 0.64 | 0.91 | 0.75 | **1.00** | 0.97 |
| Latency | 1.00 | 1.00 | 0.60 | **0.60** | 0.47 |
| Hardware | 1.00 | 1.00 | 1.00 | **1.00** | 0.30 |
| Pedagogy | 0.74 | 0.90 | 0.93 | **1.00** | 0.98 |
| **SCORE FINAL** | 0.78 | 0.91 | 0.82 | **0.90** | 0.78 |

### Décision finale

**Configuration D : Hybrid (ChromaDB + Neo4j Pedagogical) + Phi-3 + LoRA** est retenue comme architecture optimale du PFE 4.

**Justifications** :
- Score final le plus élevé (0.90).
- Meilleure QA accuracy (88%).
- Lowest hallucination rate (5%), garantissant la fiabilité pédagogique.
- Citation precision supérieure (92%), traçabilité des sources assurée.
- Latency acceptable pour utilisation interactive (250ms).
- Consommation mémoire compatible MX350 (4.2GB).
- Pedagogical score optimal (4.2/5), alignon sur objectif éducatif.

---

## Synthèse : Réduction de l'espace de recherche

| Étape | Espace initial | Espace résultant | Réduction |
|-------|---|---|---|
| COMP 1 | 54 configs | 15 configs (3 LLM × 5 retrieval-graph combos) | 72% |
| COMP 2 | 15 configs | 5 configs (1 LLM choisi, 5 retrieval-graph combos) | 67% |
| COMP 3 | 5 configs | 5 configs (1 graph choisi, testé avec tous) | 0% (parallèle) |
| COMP 4 | 5 configs | 5 configs (LLM fine-tuné, autres configs compatibles) | 0% (parallèle) |
| COMP 5 | 5 configs | **1 config** (Configuration D) | 80% |

**Temps total estimé** : 6-8 heures (vs 54 heures pour brute-force).

---

## Conclusion

Cette méthodologie en cascade garantit :
1. **Rigueur scientifique** : chaque décision est justifiée par comparaison isolée.
2. **Efficacité temporelle** : réduction de 54 à 5 configurations avant test final.
3. **Traçabilité** : chaque choix peut être expliqué et défendu devant un jury.
4. **Robustesse** : COMP 5 détecte les interactions inattendues.
5. **Adaptabilité** : si une future décision échoue, on sait où chercher les améliorations.

La configuration finale (D) balance optimalement qualité, fiabilité, performance et contraintes matérielles.
