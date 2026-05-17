# COMP2 Agents LLM Comparison

Professional benchmarking suite for evaluating 4 pedagogical agents (Architect, Writer, Enricher, Critic) across multiple LLM models using comprehensive metrics and RAGAS evaluation.

## 📋 Structure

```
benchmarking/
├── config.py                          # Central configuration (Config dataclass)
├── comp2_agents_llm_comparaison.py    # Main entrypoint (refactored)
├── prompts/                           # Externalized prompt templates
│   ├── architect.txt
│   ├── writer.txt
│   ├── enricher.txt
│   └── critic.txt
├── metrics/                           # Per-agent metrics modules
│   ├── __init__.py
│   ├── architect.py                   # Scoring: schema (30%) + modules (40%) + pedagogy (30%)
│   ├── writer.py                      # Scoring: schema (20%) + content (65%) + RAGAS (15%)
│   ├── enricher.py                    # Scoring: validity (70%) + quantity (30%)
│   └── critic.py                      # Scoring: schema (25%) + consistency (75%)
├── ragas/                             # RAGAS evaluation wrapper
│   ├── __init__.py
│   └── evaluator.py                   # LocalRagasEvaluator (Groq API + caching)
├── outputs/                           # Generated CSV results
├── cache/                             # RAGAS evaluation cache
└── README.md                          # This file
```

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies
pip install requests langchain-openai langchain-huggingface ragas datasets

# Set Groq API key
export GROQ_API_KEY="your_key_here"

# Ensure Ollama running locally
ollama serve
```

### Basic Usage
```bash
# Run all topics on all models (phi3, mistral, llama3.1)
python comp2_agents_llm_comparaison.py

# Test specific models
python comp2_agents_llm_comparaison.py --models phi3:latest,mistral:latest

# Disable RAGAS evaluation
python comp2_agents_llm_comparaison.py --no-ragas
```

## 📊 Metrics

### Configuration (`config.py`)
- **6 test topics**: Variables, Loops, Functions, Lists, Conditionals, OOP
- **2 difficulty levels**: beginner, intermediate  
- **2 age groups**: 10-13, 13-15
- **Expanded dataset**: 6 topics × 3 models = baseline for robust comparison

### Architect Metrics
- `json_valid`: Can parse as JSON (20%)
- `schema_compliance`: Has required fields (30%)
- `module_count`: At least 2 modules (20%)
- `module_completeness`: All modules structurally valid (20%)
- `pedagogical_structure`: Objectives + proper ordering (10%)

### Writer Metrics
- `schema_compliance`: Valid JSON with required fields (20%)
- `word_count`: Minimum 1500 words (15%)
- `readability`: Flesch-Kincaid grade level (10%)
- `educational_richness`: Learning keywords present (10%)
- `keyword_coverage`: Expected concepts covered (5%)
- `tone_encouragement`, `simplicity`, `engagement`: Pedagogical tone (5%)
- `ragas_*`: Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall (15%)

### Enricher Metrics
- `schema_validity`: Valid QCM structure (20%)
- `options_validity`: 4 options per question (25%)
- `answer_index_validity`: Correct answer index [0-3] (25%)
- `diversity_score`: Questions test different concepts (20%)
- `exercise_count`: At least 2 exercises (10%)

### Critic Metrics
- `schema_compliance`: Required fields present (25%)
- `score_range_validity`: Score in [0-100] (25%)
- `consistency_score`: Score matches approval status (25%)
- `issue_completeness`: Both module & global issues identified (25%)

## 🔧 Improvements Applied

### ✓ Fixed Bugs (from original code)
1. **ground_truth_type logic** - Now correctly distinguishes `human` vs `silver` vs `none`
2. **ragas_values averaging** - Filters non-numeric values ("n/a" strings) before sum()

### ✓ Architecture Improvements  
1. **Global variables → Config dataclass** - Clean centralized configuration
2. **Prompts hardcoded → External .txt files** - Easy to version, modify, test
3. **urllib → requests with retries** - Better error handling + exponential backoff
4. **Greedy regex → Non-greedy JSON extraction** - More robust parsing
5. **Isolated agents → Pipeline with content passing** - Writer output flows to Enricher/Critic
6. **Phase-based execution** - Phase 1: architect+writer, Phase 2: enricher+critic
7. **Score weights documented** - Each weight has pedagogical justification
8. **Expanded TEST_TOPICS** - 6 topics instead of 1 (scientifically valid)
9. **RAGAS caching** - Avoids redundant API calls
10. **Statistical summary** - mean ± stdev (min/max) instead of just average

### ✓ Code Quality
- **Helper function** `build_result_row()` - Eliminates repetition
- **Separated metrics modules** - architect.py, writer.py, enricher.py, critic.py (each with docs)
- **Ragas evaluator** - Ground truth strategy (human > silver > none) + caching
- **Professional docstrings** - Every function documented

## 📈 Output

CSV files generated in `outputs/`:
- `comp2_architect_models-*.csv`
- `comp2_writer_models-*.csv`
- `comp2_enricher_models-*.csv`
- `comp2_critic_models-*.csv`

Example summary output:
```
[...] phi3:latest | architect: mean=80.00 ± 5.50 (min=75, max=85)
[...] phi3:latest | writer: mean=65.33 ± 12.10 (min=55, max=78)
[...] mistral:latest | architect: mean=82.00 ± 3.20 (min=80, max=85)
```

## 🏗️ Architecture: Ground Truth Strategy

```
Writer Response Evaluation:
  1. Check cache first → Reuse if exists
  2. If reference_answer provided → Use as human ground truth
  3. Else if context_docs exist → Generate silver standard (Groq summarizes docs)
  4. Else → Only use metrics not requiring ground_truth (Faithfulness, AnswerRelevancy)
  
Output: ground_truth_type ∈ {"human", "silver", "none"}
```

## 💾 RAGAS Caching

Evaluations cached locally to avoid:
- Redundant Groq API calls
- Duplicate embeddings computation
- Unnecessary cost

Cache structure:
```
~/.cache/ragas/ragas_<md5_hash>.json
```

## 🧪 Testing

All metrics modules have been syntax-checked. To verify:
```bash
python -m py_compile config.py metrics/*.py ragas/evaluator.py comp2_agents_llm_comparaison.py
```

## 📝 Score Formula Documentation

See each metrics module docstring for detailed weight justification:
- **architect.py**: Pedagogical structure priority
- **writer.py**: Content depth + quality tone + RAGAS evidence
- **enricher.py**: Validity + diversity over quantity  
- **critic.py**: Consistency + completeness required

## 🎯 Post-PFE Usage

After benchmarking decisions, reuse prompts in production:
```python
from core.prompts_library import get_architect_prompt  # Production-grade
```

Apply insights from COMP2 metrics to improve `core/prompts_library.py` prompts.
