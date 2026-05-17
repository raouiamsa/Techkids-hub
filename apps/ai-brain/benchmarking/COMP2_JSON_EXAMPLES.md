# COMP 2 JSON Structure - Examples by Age Group

## Word Count Guidelines (Adaptive)

| Age Group | Section Content | Total | Rationale |
|-----------|-----------------|-------|-----------|
| **8-10 ans** | 100-150 words | 300-500 total | Short attention span, need visuals |
| **11-13 ans** | 150-250 words | 500-800 total | Growing comprehension, more depth |
| **14+ ans** | 250-400 words | 800-1500 total | Advanced readers, complex concepts |

---

## Example 1: Python Lists (Age 11-13)

```json
{
  "metadata": {
    "title": "Listes en Python: Stockage et Manipulation",
    "level": "beginner",
    "domain": "python",
    "age_group": "11-13",
    "estimated_duration": "15 min",
    "tags": ["structures de données", "python", "stockage"]
  },

  "learning_objectives": [
    "Créer une liste et y ajouter des éléments",
    "Accéder à un élément par son index",
    "Modifier une liste (ajouter, supprimer, remplacer)"
  ],

  "summary": {
    "short": "Une liste stocke plusieurs éléments dans l'ordre et peut être modifiée.",
    "long": "Une liste est un conteneur ordonné qui peut contenir plusieurs éléments du même type ou de types différents. Les éléments sont numérotés à partir de 0. Les listes sont modifiables (on peut ajouter, supprimer ou changer des éléments). En Python, on les crée avec des crochets [ ]."
  },

  "concept_cards": [
    {
      "id": "concept-1",
      "title": "Conteneur ordonné",
      "description": "Une liste maintient l'ordre des éléments. Le premier reste toujours le premier.",
      "icon": "📦"
    },
    {
      "id": "concept-2",
      "title": "Index (position)",
      "description": "Chaque élément a une position numérotée. En Python, on compte à partir de 0 (pas 1!).",
      "icon": "🔢"
    },
    {
      "id": "concept-3",
      "title": "Mutable (modifiable)",
      "description": "Une liste peut changer après sa création. On peut ajouter, supprimer ou modifier des éléments.",
      "icon": "✏️"
    }
  ],

  "content": {
    "markdown": "Une liste stocke plusieurs éléments...[FULL 500+ WORD MARKDOWN HERE]",
    
    "sections": [
      {
        "id": "section-1",
        "title": "Qu'est-ce qu'une liste?",
        "subtitle": "Les bases",
        "icon": "📖",
        "preview": "Une liste est comme une boîte avec des compartiments numérotés. Chaque compartiment peut contenir une information.",
        "content": "Une liste en Python est un conteneur qui stocke plusieurs éléments dans l'ordre. Imagine une boîte de rangement avec des compartiments numérotés: le premier compartiment est numéroté 0, le deuxième 1, etc. Les listes sont très utiles quand on veut stocker plusieurs valeurs liées (par exemple, une liste de prénoms d'amis, ou les scores d'une partie de jeu). La caractéristique la plus importante des listes est qu'elles sont MUTABLES, ce qui signifie qu'on peut les modifier après les avoir créées. On peut ajouter des éléments, en supprimer, ou les remplacer.",
        "word_count": 180,
        "difficulty": "easy",
        "estimated_read_time": "2 min",
        "has_visual": true,
        "has_code": false,
        "has_question": true
      },
      {
        "id": "section-2",
        "title": "Comment créer et accéder à une liste?",
        "subtitle": "Créer et lire",
        "icon": "⚙️",
        "preview": "Créer une liste est simple: utilise des crochets [ ] et sépare les éléments par des virgules. Pour accéder à un élément, utilise son index (sa position).",
        "content": "Pour créer une liste en Python, on utilise des crochets carrés [ ] et on met les éléments à l'intérieur, séparés par des virgules. Par exemple: fruits = ['pomme', 'banane', 'orange']. Pour accéder à un élément, on utilise son index entre crochets. ATTENTION: en Python, on compte à partir de 0! Donc 'pomme' est à l'index 0, 'banane' à l'index 1, et 'orange' à l'index 2. Si tu veux le premier élément, tu écris fruits[0]. Si tu veux le dernier, tu peux utiliser fruits[-1].",
        "word_count": 190,
        "difficulty": "easy",
        "estimated_read_time": "3 min",
        "has_visual": true,
        "has_code": true,
        "has_question": true
      },
      {
        "id": "section-3",
        "title": "Modifier une liste",
        "subtitle": "Ajouter, supprimer, remplacer",
        "icon": "💡",
        "preview": "Les listes peuvent changer! Tu peux ajouter de nouveaux éléments avec .append(), les supprimer avec .remove(), ou en remplacer avec l'index.",
        "content": "Puisque les listes sont mutables, on peut les modifier de plusieurs façons. Pour ajouter un élément à la fin, on utilise .append(). Par exemple: fruits.append('raisin') ajoute 'raisin' à la fin de la liste. Pour supprimer un élément, on utilise .remove() en mettant l'élément qu'on veut supprimer: fruits.remove('banane') enlève 'banane'. Pour remplacer un élément, on utilise son index: fruits[1] = 'kiwi' remplace le deuxième élément. On peut aussi utiliser .pop() pour enlever et récupérer le dernier élément.",
        "word_count": 200,
        "difficulty": "medium",
        "estimated_read_time": "3 min",
        "has_visual": true,
        "has_code": true,
        "has_question": false
      }
    ]
  },

  "code_examples": [
    {
      "language": "python",
      "title": "Créer une liste de fruits",
      "code": "fruits = ['pomme', 'banane', 'orange']\nprint(fruits)\nprint(fruits[0])\nprint(fruits[-1])",
      "explanation": "On crée une liste de 3 fruits. print(fruits) affiche toute la liste. fruits[0] affiche le premier élément. fruits[-1] affiche le dernier.",
      "output_expected": "['pomme', 'banane', 'orange']\npomme\norange"
    },
    {
      "language": "python",
      "title": "Modifier une liste",
      "code": "fruits = ['pomme', 'banane']\nfruits.append('orange')\nfruits.remove('banane')\nfruits[0] = 'raisin'\nprint(fruits)",
      "explanation": "On ajoute une orange, on enlève la banane, on remplace la pomme par un raisin.",
      "output_expected": "['raisin', 'orange']"
    }
  ],

  "visual_aids": [
    {
      "type": "diagram",
      "title": "Structure d'une liste",
      "description": "Diagramme montrant comment les éléments d'une liste sont indexés de 0 à n",
      "url_or_placeholder": "List indexing diagram (0-based)"
    }
  ],

  "quiz": [
    {
      "id": "quiz-1",
      "question": "Quel est l'index du deuxième élément d'une liste?",
      "answer": "1",
      "choices": ["0", "1", "2"],
      "difficulty": "easy",
      "explanation": "En Python, on compte à partir de 0. Le premier élément est à l'index 0, donc le deuxième est à l'index 1."
    },
    {
      "id": "quiz-2",
      "question": "Quelle méthode ajoute un élément à la fin d'une liste?",
      "answer": ".append()",
      "choices": [".add()", ".append()", ".insert()"],
      "difficulty": "medium",
      "explanation": ".append() ajoute toujours à la fin. .insert() peut insérer à une position spécifique. .add() n'existe pas pour les listes."
    }
  ],

  "exercises": [
    {
      "id": "exercise-1",
      "type": "code",
      "title": "Crée ta liste de films préférés",
      "instructions": "Crée une liste contenant tes 3 films préférés, puis affiche le premier et le dernier film.",
      "starterCode": "# Crée ta liste de films\nfilms = # TODO: ajoute 3 films\n\n# Affiche le premier film\nprint(films[0])\n\n# Affiche le dernier film\nprint(films[-1])",
      "solution": "films = ['Toy Story', 'Avatar', 'Coco']\nprint(films[0])\nprint(films[-1])",
      "hints": [
        "Utilise des crochets [ ] et sépare tes films par des virgules",
        "films[0] affiche le premier film",
        "films[-1] affiche le dernier film"
      ],
      "difficulty": "easy",
      "estimated_time": "5 min"
    },
    {
      "id": "exercise-2",
      "type": "code",
      "title": "Modifie ta liste",
      "instructions": "À partir de ta liste de films, ajoute un 4e film, puis remplace le 2e film.",
      "starterCode": "films = ['Toy Story', 'Avatar', 'Coco']\n\n# TODO: Ajoute un 4e film\n# TODO: Remplace le 2e film",
      "solution": "films = ['Toy Story', 'Avatar', 'Coco']\nfilms.append('Frozen')\nfilms[1] = 'The Lion King'\nprint(films)",
      "hints": [
        "Utilise .append() pour ajouter à la fin",
        "Utilise films[1] pour remplacer le 2e film",
        "Rappel: le compte commence à 0!"
      ],
      "difficulty": "medium",
      "estimated_time": "7 min"
    }
  ],

  "warnings": [
    {
      "type": "attention",
      "message": "En Python, le comptage commence à 0! Le premier élément est à l'index 0, pas 1."
    },
    {
      "type": "error_prone",
      "message": "Si tu accèdes à un index qui n'existe pas (par exemple fruits[5] quand la liste n'a que 3 éléments), tu auras une erreur IndexError."
    }
  ],

  "call_to_action": {
    "label": "Essaie maintenant!",
    "action": "start_exercises"
  }
}
```

---

## Age Group Adaptations Summary

### 8-10 ans:
- Sections: 100-150 words each
- More emojis, simpler language
- Visuals in every section
- Exercises are drag-drop or very simple code
- Quiz: 1-2 questions max

### 11-13 ans:
- Sections: 150-250 words each
- Mix of explanation + examples
- 1-2 visuals per section (not every section)
- Exercises: simple code or fill-blanks
- Quiz: 2-3 questions

### 14+ ans:
- Sections: 250-400 words each
- More technical depth
- Visuals as needed (not required)
- Exercises: complex code projects
- Quiz: 3+ questions, nuanced answers

---

## COMP 2 Validation Rules

For each section:
```
✓ word_count within age range
✓ has preview (always visible)
✓ has content (age-appropriate length)
✓ has_visual OR has_code OR has_question = true
✓ difficulty level is appropriate
✓ estimated_read_time matches word_count

Score per section = (requirements met / total requirements) × 100
Final score = average of all sections
```

---

## COMP 2 Evaluation Layers

The COMP 2 pipeline is evaluated on three distinct layers so that each failure mode can be diagnosed precisely.

### 1. RAG Layer

This layer measures whether the retrieval step brought the right context before generation.

Main metrics:

- `retrieval_latency_ms`
- `retrieved_docs_count`
- `context_coverage_pct`
- `ragas_context_precision`
- `ragas_context_recall`

Mandatory metrics:

- `ragas_faithfulness`
- `ragas_answer_relevancy`

### 2. LLM Layer

This layer measures the raw generation behavior of the model.

Main metrics:

- `llm_latency_ms`
- `ttft_ms`
- `instruction_adherence_pct`
- `format_strictness_pct`
- `hallucination_rate_pct`

### 3. Agent Layer

This layer measures whether each role succeeded in its task.

Main metrics:

- `json_valid`
- `schema_compliance`
- `role_specific_quality`
- `score`

---

## Per-Agent Metric Map

### Architect

Purpose: build the syllabus / course structure.

Metrics:

- `json_valid`
- `schema_compliance`
- `module_count`
- `module_completeness_pct`
- `pedagogical_structure_score`

How the score is read:

- JSON valid means the output can be parsed.
- Schema compliance means the required fields exist: `courseTitle`, `modules`, `level`, `programmingLanguage`.
- Module completeness measures how many modules contain `title`, `description`, and `subTopics`.
- Pedagogical structure checks that objectives exist and that the order follows a logical progression.

### Writer

Purpose: generate the pedagogical content.

Metrics:

- `json_valid`
- `schema_compliance`
- `word_count`
- `readability_score`
- `educational_richness_score`
- `keyword_coverage_pct`
- `ragas_faithfulness`
- `ragas_answer_relevancy`

How the score is read:

- Word count checks whether the content length matches the age group.
- Readability measures how easy the text is to read.
- Educational richness checks for examples, practice, tips, and explanations.
- Keyword coverage measures whether expected pedagogical keywords are present.
- RAGAS faithfulness checks whether the answer stays grounded in the retrieved context.
- RAGAS answer relevancy checks whether the content actually answers the target task.

### Enricher

Purpose: generate QCMs and exercises.

Metrics:

- `json_valid`
- `schema_validity_pct`
- `exercise_count`
- `options_validity_pct`
- `answer_index_validity_pct`
- `diversity_score`

How the score is read:

- Schema validity checks that each question has `question`, `options`, `correct_index`, and `explanation`.
- Options validity checks that each question has exactly 4 options.
- Answer index validity checks that `correct_index` is between 0 and 3.
- Diversity checks that questions are not duplicates.

### Critic

Purpose: audit the generated module.

Metrics:

- `json_valid`
- `schema_compliance`
- `score_range_validity`
- `consistency_score`
- `issue_completeness`

How the score is read:

- Score range validity checks that the critic score stays between 0 and 100.
- Consistency checks that score and approval are logically aligned.
- Issue completeness checks that the critic provides both module issues and global issues.

---

## Why we keep both metrics and a score

Metrics explain the cause of a failure.

Score gives one number that is easy to compare across models.

Recommended aggregation:

- `RAG Score` = weighted average of retrieval metrics
- `LLM Score` = weighted average of raw model metrics
- `Agent Score` = weighted average of the role-specific metrics
- `Final Score` = `0.2 * RAG + 0.3 * LLM + 0.5 * Agent`

This lets COMP 2 answer three questions at once:

1. Did the retrieval work?
2. Did the model generate correctly?
3. Did the agent succeed in its role?

---

## Agent Responsibilities

| Agent | Creates/Fills | Validates |
|-------|---------------|-----------|
| **Architect** | metadata, learning_objectives, summary | Structure present |
| **Writer** | content (sections + markdown) | Word counts, engagement |
| **Enricher** | quiz, exercises, concept_cards | Quality + variety |
| **Critic** | evaluation field | Overall coherence + score |

---

## COMP 2 Summary For Report

If you need a short academic description:

> COMP 2 evaluates the pedagogical generation pipeline at three levels: retrieval quality, raw model behavior, and agent task success. RAGAS is used to measure context grounding for the writer, while agent-specific heuristics measure JSON validity, schema compliance, completeness, and pedagogical quality.
