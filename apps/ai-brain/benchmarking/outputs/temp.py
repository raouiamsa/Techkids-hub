import csv
with open('comp1_retrieval_ablation_summary_intfloat_multilingual-e5-small_cs1000_co150.csv') as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r['evaluation_k'] == '5' and r['strategy'] in ['Chroma (Vector) k=5', 'Neo4j (Vector) k=5', 'Neo4j (Graph) k=5', 'Neo4j (Hybrid) k=5 tc=def w=50/50 rrf=60 reranker=lexical']:
            print(f"{r['strategy']} | MRR: {r['mrr'][:5]} | Recall: {r['recall_at_k'][:5]} | NDCG: {r['ndcg_at_k'][:5]} | Latency: {float(r['latency_ms']):.1f}ms")
