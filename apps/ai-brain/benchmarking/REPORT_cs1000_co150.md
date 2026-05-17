# Final Report — Selected Chunking: cs1000_co150

## Summary

- **Choice:** cs1000_co150 (chunk size 1000 tokens, overlap 150 tokens).
- **Retrieval Strategy:** Hybrid Neo4j (vector + graph) with lexical reranking.
- **Parameters:**
  - Limit (top-k results): 5
  - Weights: vector=0.6, graph=0.4
  - RRF k-parameter: 60
  - Reranker: lexical
- **Files:** Outputs and diagnostics available in `apps/ai-brain/benchmarking/outputs/`.

## Winning Configuration Metrics

From COMP 1 ablation (line: Neo4j Hybrid k=5 tc=def w=60/40 rrf=60):
- **Recall@5:** 0.9
- **Precision@5:** 0.534
- **MRR:** 0.8
- **nDCG@5:** 0.8
- **Coverage:** 0.513
- **Latency:** 41.66 ms

## Academic Justification

cs1000_co150 represents a principled trade-off between semantic coherence and retrieval granularity. Chunks of ~1000 tokens preserve substantial intra-document context (paragraph-to-section continuity) so that dense embeddings capture robust topical signals, while a 150-token overlap mitigates boundary effects where relevant information straddles adjacent chunks. Empirically, this configuration yields higher effective coverage (chunk-aware token coverage with embedding-fallback) without incurring the index fragmentation and candidate dilution observed at smaller chunk sizes, nor the reduced recall at coarser chunkings where relevant passages are pooled into overly large segments.

The hybrid retrieval strategy combines vector similarity search and graph-based concept matching via Reciprocal Rank Fusion. The selected weights (vector=0.6, graph=0.4) favor vector retrieval while retaining the structured benefits of graph reasoning. This configuration maximizes per-chunk semantic density—improving embedding quality and reranker utility—while maintaining a manageable candidate pool size for efficient fusion.

## Practical Notes & Next Steps

- The strategy is now fixed for COMP 2–5 comparisons (LLM selection, fine-tuning, integration testing).
- Configuration stored in `strategy_final.json` for reproducibility and referencing in future runs.
- All LLMs in COMP 2 and beyond will receive the same 5 retrieved documents, ensuring fair comparison.

---

Report generated on 2026-05-09.
