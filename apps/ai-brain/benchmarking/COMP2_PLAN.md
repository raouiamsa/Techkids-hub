# COMP 2: LLM Baselines Comparison — Detailed Plan

## 1. Objectifs

Sélectionner le **meilleur modèle de génération brut** pour générer du contenu pédagogique avant fine-tuning.

**Critères de sélection:**
- Qualité de génération (BLEU, ROUGE-L, BERTScore)
- Stabilité (hallucination rate, citation precision)
- Performance (latency, memory usage)

## 2. Configuration Fixée (du Winner COMP 1)

Fichier: `strategy_final.json`

```json
{
  "retrieval": {
    "backend": "hybrid",
    "limit": 5,
    "reranker": "lexical",
    "weights": {"vector": 0.6, "graph": 0.4},
    "rrf_k": 60
  }
}
```

**Interprétation:**
- Chaque question reçoit exactement 5 documents pertinents
- Ces 5 documents sont le contexte du LLM
- Tous les LLMs reçoivent le même ensemble de documents → comparaison équitable

## 3. Modèles à Comparer

| Modèle | Provider | Taille | Notes |
|--------|----------|--------|-------|
| **Phi-3** | Microsoft | ~7B / ~14B | Léger, adapté pédagogie |
| **Mistral** | Mistral AI | ~7B | Performant, balance |
| **Llama** | Meta | ~7B / ~13B | Large community |

**Variantes testées:** Versions 7B par défaut (pas de 13B+ pour contrôler les ressources).

## 4. Dataset

Fichier: `apps/ai-brain/benchmarking/dataset/sprint4_comp1_testcases.json`

**Structure:**
```json
{
  "question_id": 1,
  "question": "Qu'est-ce qu'une liste en Python ?",
  "reference_answer": "Une liste est une structure ordonnée...",
  "relevant_documents": ["python_lists_web", "python_basics_pdf"],
  "concepts": ["list", "ordered", "mutable"],
  "domain": "Python",
  "difficulty": "easy"
}
```

**Taille recommandée:** ~20-30 questions pour chaque modèle (contrôle du temps).

## 5. Architecture du Runner

**Fichier:** `apps/ai-brain/benchmarking/comp2_llm_baseline_runner.py`

### 5.1 Entrées
```python
{
  "model_name": "phi-3",  # ou mistral, llama
  "model_variant": "7b",
  "test_limit": 20,  # nombre de questions à tester
  "retrieval_config": strategy_final.json["retrieval"]
}
```

### 5.2 Processus pour chaque question

```
1. question → retrieval.search_hybrid() → 5 documents
2. context = format_documents(5 docs)
3. prompt = f"""Contexte:\n{context}\n\nQuestion: {question}\nRéponse:"""
4. generated_answer = llm.generate(prompt)
5. Calculer métriques(generated_answer, reference_answer)
6. Enregistrer logs et résultats
```

### 5.3 Sorties

Fichier CSV: `apps/ai-brain/benchmarking/outputs/comp2_llm_baseline_summary_{model_name}_{timestamp}.csv`

```
question_id,model,question,reference_answer,generated_answer,bleu,rouge_l,bertscore,hallucination_rate,citation_precision,latency_ms,memory_mb
1,phi-3,"Qu'est-ce qu'une liste ?","Une liste est...", "Une liste est...",0.65,0.72,0.78,0.0,1.0,125,2048
...
```

## 6. Métriques Détaillées

### 6.1 BLEU (Bilingual Evaluation Understudy)
- **Calcul:** Similarité lexicale n-gram entre généré et référence
- **Plage:** 0-1 (1 = identique)
- **Interprétation:** Capture la similarité exacte du wording
- **Bibliothèque:** `nltk.translate.bleu_score`

### 6.2 ROUGE-L (Recall-Oriented Understudy for Gisting Evaluation)
- **Calcul:** Longest common subsequence normalisée
- **Plage:** 0-1 (1 = couverture totale)
- **Interprétation:** Qualité de couverture des concepts clés
- **Bibliothèque:** `rouge_score` (pip install rouge-score)

### 6.3 BERTScore
- **Calcul:** Similarité sémantique contextuelle via embeddings BERT
- **Plage:** 0-1 (1 = identique sémantiquement)
- **Interprétation:** La plus fiable pour qualité sémantique
- **Bibliothèque:** `bert_score` (pip install bert-score)

### 6.4 Hallucination Rate
- **Calcul:** Détection de contenus générés non présents dans contexte/référence
- **Heuristique:** Mots-clés du contexte doivent être couverts par la réponse
- **Approche simple:** Compter % de phrases sans source dans contexte
- **Plage:** 0-1 (0 = pas de hallucination)

### 6.5 Citation Precision
- **Calcul:** % de citations correctes par rapport aux documents fournis
- **Heuristique:** Mots clés du contexte + source validation
- **Plage:** 0-1 (1 = toutes les citations sont correctes)

### 6.6 Latency
- **Calcul:** `time.perf_counter()` avant/après génération
- **Unité:** millisecondes (ms)
- **Interprétation:** Temps d'inférence réel

### 6.7 Memory Usage
- **Calcul:** `psutil.Process().memory_info().rss` au pic
- **Unité:** MB ou GB
- **Interprétation:** RAM/VRAM utilisée pendant inférence

## 7. Résumé Attendu

Agrégation par modèle (moyenne sur toutes les questions):

```
Model     | BLEU | ROUGE-L | BERTScore | Hallucination | Citation Precision | Latency (ms) | Memory (GB)
----------|------|---------|-----------|---------------|--------------------|--------------|------------
Phi-3     | 0.68 | 0.74    | 0.82      | 0.08          | 0.92               | 125          | 4.2
Mistral   | 0.65 | 0.71    | 0.80      | 0.12          | 0.88               | 150          | 6.1
Llama     | 0.62 | 0.68    | 0.78      | 0.15          | 0.85               | 180          | 7.8
```

**Décision:** Choisir basé sur le **score composite:**
```
score = (BLEU + ROUGE_L + BERTScore) / 3 - (Hallucination * 0.5) - (Latency / 200)
```

Favoriser Phi-3 si proche (léger et rapide).

## 8. Implémentation Progressive

### Phase 1: Configuration
- [ ] Créer `comp2_llm_baseline_runner.py`
- [ ] Charger `strategy_final.json`
- [ ] Initialiser retrieval
- [ ] Installer dépendances (nltk, rouge-score, bert-score, psutil)

### Phase 2: Intégration LLM
- [ ] Charger modèles (Phi-3, Mistral, Llama)
- [ ] Test simple: 1 question par modèle
- [ ] Vérifier format des réponses

### Phase 3: Métriques
- [ ] Implémenter BLEU, ROUGE-L
- [ ] Implémenter BERTScore
- [ ] Implémenter détection hallucination (heuristique simple)
- [ ] Implémenter citation precision (heuristique)

### Phase 4: Exécution
- [ ] Boucler sur 20 questions, 3 modèles
- [ ] Enregistrer CSV de résultats détaillés
- [ ] Générer résumé par modèle
- [ ] Visualiser (courbes, tables)

### Phase 5: Analyse & Décision
- [ ] Lire résumé
- [ ] Comparer score composite
- [ ] Documenter choix du gagnant
- [ ] Enregistrer dans `comp2_winner.json`

## 9. Ressources Estimées

| Étape | Durée | Ressource |
|-------|-------|-----------|
| Phase 1-2 (setup) | 1-2h | Développement |
| Phase 3 (métriques) | 2-3h | Implémentation |
| Phase 4 (exécution 20 questions × 3 modèles) | 3-6h | GPU/CPU |
| Phase 5 (analyse) | 1h | Analyse |
| **Total** | **7-12h** | |

## 10. Sorties Finales

1. **CSV détaillé:** `comp2_llm_baseline_summary_{model}_{timestamp}.csv`
2. **Résumé agrégé:** `comp2_baseline_results_summary.md` (table + scores)
3. **Décision:** `comp2_winner.json` (modèle sélectionné + justification)
4. **Rapport:** `COMP2_ANALYSIS.md` (analyse complète)

---

**Prochaines étapes:** Implémenter Phase 1 et Phase 2 du runner.
