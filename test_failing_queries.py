"""Quick diagnostic to see what's being retrieved for failing queries"""
import sys
sys.path.insert(0, 'src')

from src.rag_langchain import search_sentences

queries = [
    "What is the exact financial approval limit for DDWP in the 2024 Manual?",
    "Give me the official definition of 'throw-forward' exactly as written in the Manual"
]

for query in queries:
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print('='*80)
    
    try:
        chunks = search_sentences(query, top_k=5)
        
        print(f"\nRetrieved {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- Chunk {i} (Score: {chunk.get('rerank_score', chunk.get('score', 0)):.3f}) ---")
            text = chunk.get('text', '')
            print(text[:300])
            
            # Check for key terms
            has_ddwp = 'DDWP' in text or 'ddwp' in text.lower()
            has_limit = 'limit' in text.lower() or 'rs.' in text.lower() or 'million' in text.lower()
            has_throwforward = 'throw-forward' in text.lower() or 'throw forward' in text.lower()
            
            if has_ddwp and has_limit:
                print("\n✅ Contains DDWP + limit/amount")
            if has_throwforward:
                print("\n✅ Contains throw-forward")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
