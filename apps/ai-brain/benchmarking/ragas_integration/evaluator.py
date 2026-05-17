# benchmarking/ragas/evaluator.py
"""Local RAGAS evaluator using Groq API for ground truth generation."""

import json
import hashlib
from typing import Dict, List, Optional
from pathlib import Path
import os

try:
    from datasets import Dataset
    from ragas import evaluate
    try:
        from ragas import RunConfig
    except ImportError:
        from ragas.run_config import RunConfig  # type: ignore
    from ragas.metrics import (  # type: ignore
        Faithfulness,
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
    )
    from langchain_groq import ChatGroq
    from langchain_huggingface import HuggingFaceEmbeddings

    RAGAS_AVAILABLE = True
except ImportError as _e:
    RAGAS_AVAILABLE = False
    _RAGAS_IMPORT_ERROR = str(_e)


class LocalRagasEvaluator:
    """Evaluate LLM responses using RAGAS metrics via Groq API.
    
    Features:
    - Ground truth strategy: Human > Silver (auto-generated) > None
    - Caching: Stores evaluations locally to avoid redundant API calls
    - Metrics: Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mixtral-8x7b-32768",
        cache_dir: Optional[Path] = None,
        use_cache: bool = True
    ):
        """Initialize RAGAS evaluator.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Groq model to use
            cache_dir: Directory for caching evaluations
            use_cache: Whether to use caching
        """
        if not RAGAS_AVAILABLE:
            detail = globals().get("_RAGAS_IMPORT_ERROR", "unknown import error")
            raise RuntimeError(
                f"RAGAS not available ({detail}). "
                "Install with: pip install ragas langchain-openai langchain-huggingface"
            )

        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not set. Set env var GROQ_API_KEY or pass api_key parameter.")

        self.model = model
        self.use_cache = use_cache
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "ragas"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize LLM (ChatGroq)
        self.llm = ChatGroq(
            model=model,
            temperature=0.0,
            api_key=self.api_key,
            timeout=60,
            max_retries=2,
        )

        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-small",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Metrics
        self.metrics_no_gt = [
            Faithfulness(llm=self.llm),
            AnswerRelevancy(llm=self.llm),
        ]
        self.metrics_with_gt = [
            ContextPrecision(llm=self.llm),
            ContextRecall(llm=self.llm),
        ]

    def _get_cache_path(self, key: str) -> Path:
        """Generate cache file path from key."""
        hash_val = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"ragas_{hash_val}.json"

    def _get_cache_key(self, question: str, answer: str, context: str, ground_truth: str) -> str:
        """Generate optimized cache key (truncated for memory efficiency).
        
        FIX #8: Avoid storing huge strings in memory
        """
        # Truncate large fields to avoid memory bloat before hashing
        raw = json.dumps({
            "q": question[:2000],  # Truncate large questions
            "a": answer[:5000],    # Truncate large answers
            "c": context[:5000],   # Truncate large contexts
            "gt": ground_truth[:5000]  # Truncate large ground truth
        }, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    def _load_cache(self, key: str) -> Optional[Dict]:
        """Load cached evaluation."""
        if not self.use_cache:
            return None

        cache_file = self._get_cache_path(key)
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text())
            except Exception:
                return None
        return None

    def _save_cache(self, key: str, result: Dict) -> None:
        """Save evaluation to cache."""
        if not self.use_cache:
            return

        cache_file = self._get_cache_path(key)
        try:
            cache_file.write_text(json.dumps(result, indent=2))
        except Exception:
            pass  # Silently fail cache write

    def generate_silver_ground_truth(
        self,
        context_docs: List[str],
        topic: str
    ) -> str:
        """Generate silver-standard ground truth from source documents.
        
        When human reference answers are unavailable, summarize the retrieved
        documents into an ideal response. This is academically valid (based on
        real sources, but not written by a human expert).
        
        Args:
            context_docs: List of retrieved document snippets
            topic: Topic for context
            
        Returns:
            Generated ground truth text
        """
        if not context_docs:
            return ""

        context_text = "\n\n".join(context_docs[:3])[:6000]  # Top-3 docs, max 6000 chars
        prompt = (
            f'Tu es un expert pédagogique. '
            f'En te basant UNIQUEMENT sur ces documents sur "{topic}", '
            f'rédige en 2-3 paragraphes une réponse idéale qui résume les concepts '
            f'clés qu\'un débutant doit connaître.\n\nDocuments:\n{context_text}\n\nRéponse idéale:'
        )

        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception:
            # Fallback: concat docs
            return "\n\n".join(context_docs)

    def evaluate_generation(
        self,
        question: str,
        answer: str,
        context: str,
        ground_truth: str = "",
        context_docs: Optional[List[str]] = None,
        topic: str = "",
    ) -> Dict:
        """Evaluate LLM generation using RAGAS metrics.
        
        Args:
            question: Input question
            answer: LLM-generated answer
            context: Retrieved context (legacy, for caching)
            ground_truth: Optional human-provided reference answer
            context_docs: Optional list of retrieved docs (for silver generation)
            topic: Topic (for silver generation context)
            
        Returns:
            Dict with metrics and ground_truth_type
        """
        # Check cache first (FIX #8: use optimized cache key)
        cache_key = self._get_cache_key(question, answer, context, ground_truth)
        cached = self._load_cache(cache_key)
        if cached:
            return cached

        # Determine ground truth strategy
        has_explicit_gt = bool(ground_truth and str(ground_truth).strip())
        generated_silver = False

        # Generate silver standard if no explicit GT but we have docs
        if not has_explicit_gt and context_docs:
            generated_silver = True
            ground_truth = self.generate_silver_ground_truth(context_docs, topic)

        has_ground_truth = bool(ground_truth and str(ground_truth).strip())

        # Select applicable metrics
        active_metrics = self.metrics_no_gt + (self.metrics_with_gt if has_ground_truth else [])

        # Build dataset (FIX #6: pass contexts as list, not single string)
        dataset_dict = {
            "question": [question],
            "answer": [answer],
            "contexts": [context_docs if context_docs else [context[:15000]]],  # Pass list of docs
        }
        if has_ground_truth:
            dataset_dict["ground_truth"] = [ground_truth[:15000]]

        dataset = Dataset.from_dict(dataset_dict)

        # Evaluate
        # BUG #7 FIX: Lower timeout from 300s to 120s (5min was too much for 18 evals)
        run_config = RunConfig(timeout=120, max_retries=2)
        result = evaluate(
            dataset=dataset,
            metrics=active_metrics,
            llm=self.llm,
            embeddings=self.embeddings,
            run_config=run_config,
            batch_size=1,
        )

        scores = result.to_pandas().mean(numeric_only=True).to_dict()

        # FIX #3: Handle metric name variations (answer_relevancy vs answer_relevance)
        output = {
            "faithfulness": round(scores.get("faithfulness", 0.0), 4),
            "answer_relevancy": round(scores.get("answer_relevancy", scores.get("answer_relevance", 0.0)), 4),
            "context_precision": round(scores.get("context_precision", 0.0), 4) if has_ground_truth else "n/a",
            "context_recall": round(scores.get("context_recall", 0.0), 4) if has_ground_truth else "n/a",
            "ground_truth_type": (
                "silver" if generated_silver
                else ("human" if has_explicit_gt else "none")
            ),
        }

        # Cache result
        self._save_cache(cache_key, output)

        return output
