#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test RAG retrieval directly to diagnose the issue
"""
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 70)
print("RAG DIRECT TEST")
print("=" * 70)
print()

# Initialize
print("Loading embedding model...")
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
qdrant_client = QdrantClient(host='localhost', port=6333)
print("OK - Model and Qdrant loaded")
print()

# Test queries
test_queries = [
    "Jaki zasieg ma Model 3 Long Range?",
    "Czy moge dostac doplaty do zakupu Tesli?",
    "Jakie sa koszty serwisu Tesli?",
]

for query in test_queries:
    print(f"Query: {query}")
    print("-" * 70)

    # Generate embedding
    query_embedding = embedding_model.encode(query).tolist()

    # Search with different thresholds
    for threshold in [0.50, 0.60, 0.70, 0.75]:
        results = qdrant_client.search(
            collection_name="ultra_rag_v1",
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="language",
                        match=models.MatchValue(value="pl")
                    )
                ]
            ),
            limit=3,
            score_threshold=threshold
        )

        print(f"  Threshold {threshold}: {len(results)} results")
        if results:
            for idx, result in enumerate(results, 1):
                title = result.payload.get("title", "N/A")[:50]
                print(f"    {idx}. Score: {result.score:.4f} - {title}")

    print()

print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
