import sys
from pathlib import Path

# Ensure parent package (apps/ai-brain) is on sys.path so we can import benchmarking
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmarking.strategy_final import get_final_strategy, get_retriever_from_strategy
from benchmarking.comp2_agents_llm_comparaison import retrieve_context_documents

if __name__ == '__main__':
    strategy = get_final_strategy()
    retr = get_retriever_from_strategy(strategy)
    docs = retrieve_context_documents(retr, 'python', limit=5)
    print('\n---DOCS START---\n')
    for i,d in enumerate(docs[:3],1):
        print(f'--- Doc {i} ---\n')
        print(d[:400])
        print('\n')
    print('---DOCS END---\n')
    silver = '\n\n'.join(docs[:3])
    print('\n---SILVER GT (fallback concat)---\n')
    print(silver[:2000])
