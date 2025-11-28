"""
ULTRA v3.1 - Simple RAG Test (Synchronous)
"""
import sys
sys.path.insert(0, 'backend')

print("=" * 70)
print("ULTRA v3.1 - RAG TEST")
print("=" * 70)

try:
    print("\n[1/4] Importing RAG engine...")
    from rag_engine import rag_engine
    print("✅ Import successful")
    
    print("\n[2/4] Checking RAG engine status...")
    if not rag_engine.client:
        print("❌ Qdrant client not initialized")
        sys.exit(1)
    if not rag_engine.model:
        print("❌ Embedding model not loaded")
        sys.exit(1)
    print("✅ RAG engine ready")
    
    print("\n[3/4] Performing search...")
    query = "Klient martwi się, że zimą zasięg drastycznie spadnie."
    print(f"Query: '{query}'")
    
    results = rag_engine.search(query, limit=4)
    
    print(f"\n[4/4] Results: Found {len(results)} nuggets")
    print("=" * 70)
    
    if not results:
        print("\n❌ NO RESULTS - Check if Qdrant collection has data")
        sys.exit(1)
    
    for i, r in enumerate(results, 1):
        print(f"\nNUGGET #{i}:")
        print(f"  Score: {r.get('score', 0):.2f}")
        print(f"  Source: {r.get('source', '?')}")
        print(f"  Title: {r.get('title', r.get('trigger_context', ''))[:60]}...")
        print(f"  Content: {r.get('content', r.get('golden_response', ''))[:100]}...")
    
    print("\n" + "=" * 70)
    print("✅ TEST PASSED - RAG is working!")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
