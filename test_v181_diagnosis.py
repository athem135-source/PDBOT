"""
v1.8.1 Diagnostic: Check if numeric preservation is actually working
"""
import sys
sys.path.insert(0, 'src')

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Initialize
qc = QdrantClient(url="http://localhost:6338")
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Test queries
queries = [
    "What is the DDWP approval limit?",
    "What is the CDWP approval limit?",
    "What is the ECNEC threshold?"
]

print("=" * 80)
print("v1.8.1 DIAGNOSTIC: Checking Retrieved Chunks")
print("=" * 80)

for query in queries:
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print('='*80)
    
    # Embed query
    query_vec = embedder.encode(query).tolist()
    
    # Search
    results = qc.search(
        collection_name="pnd_manual_v2",
        query_vector=query_vec,
        limit=5,
        score_threshold=0.15
    )
    
    print(f"\nRetrieved {len(results)} chunks:")
    
    for i, hit in enumerate(results, 1):
        print(f"\n--- Chunk {i} (Score: {hit.score:.3f}, Page: {hit.payload.get('page_number', 'N/A')}) ---")
        chunk_text = hit.payload.get('text', '')
        print(chunk_text[:500])  # First 500 chars
        
        # Check for numeric patterns
        has_rs = 'Rs.' in chunk_text or 'rupees' in chunk_text.lower()
        has_million = 'million' in chunk_text.lower()
        has_billion = 'billion' in chunk_text.lower()
        
        if has_rs or has_million or has_billion:
            print(f"\n✅ CONTAINS NUMERIC VALUE: Rs={has_rs}, Million={has_million}, Billion={has_billion}")
        else:
            print(f"\n❌ NO NUMERIC VALUE DETECTED")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
