---
title: Final Report — cs1000_co150
---

# Final Report: cs1000_co150

- Choice: cs1000_co150
- Reranker: lexical
- Fusion: hybrid vector+graph (weights 50/50)
- Candidate pool: 200 (vector 150 / graph 150)

---

## Academic Justification

cs1000_co150 balances semantic coherence and retrieval granularity. 1000-token chunks keep topical context; 150-token overlap reduces boundary misses. Embedding-fallback coverage shows better effective recall versus smaller or coarser chunkings.

---

## Metrics Observed

- Recall@K: improved across hybrid strategies
- MRR & nDCG: higher for cs1000_co150
- Coverage (token-aware + embedding fallback): stable and higher than alternatives

---

## Practical Notes

- Cross-encoder: tested but removed (too slow); keep lexical reranker for production.
- To validate final results: run targeted cross-encoder rerank on top-100 candidates only (optional).

---

## Next Steps

1. Use `strategy_final.json` as canonical config in future runs.
2. Commit strategy and report.
3. If needed, run cross-encoder verification on a smaller sample.

---

_Report generated 2026-05-08_
