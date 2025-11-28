import asyncio
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Setup
client = QdrantClient("http://localhost:6333")
collection_name = "ultra_knowledge"
model = SentenceTransformer('all-MiniLM-L6-v2')

async def run_test():
    output_lines = []
    output_lines.append("=" * 70)
    output_lines.append("ULTRA v3.1 - DIAGNOSTIC REPORT")
    output_lines.append("=" * 70)
    
    # 1. CHECK COUNT
    count = client.count(collection_name=collection_name)
    output_lines.append(f"\n📉 Vector Count: {count.count} (Expected: ~11,000)")
    
    if count.count < 10000:
        output_lines.append(f"⚠️  WARNING: Only {count.count} vectors found!")
        output_lines.append("   Expected 7,710 + 3,840 = 11,550 items")
        output_lines.append("   Possible ingestion failure!")

    # 2. CHECK RETRIEVAL (The Winter Test)
    query = "Klient martwi się o zasięg zimą i pompę ciepła."
    output_lines.append(f"\n🔍 Query: {query}")
    output_lines.append("")
    
    vector = model.encode(query).tolist()
    results = client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=3
    )

    output_lines.append(f"💡 Top 3 Results:")
    output_lines.append("=" * 70)
    
    for i, hit in enumerate(results):
        output_lines.append(f"\n[Result {i+1}] Score: {hit.score:.4f}")
        # Print Payload safely
        payload = hit.payload
        output_lines.append(f"  Title: {payload.get('title', 'No Title')}")
        output_lines.append(f"  Source: {payload.get('source', 'unknown')}")
        output_lines.append(f"  ID: {payload.get('id', 'No ID')}")
        content = payload.get('content', payload.get('golden_response', 'No Content'))
        output_lines.append(f"  Content Preview: {content[:150]}...")
        output_lines.append("")
    
    output_lines.append("=" * 70)
    output_lines.append("END DIAGNOSTIC REPORT")
    output_lines.append("=" * 70)
    
    # Write to file with UTF-8 encoding
    with open('diagnostic_report.txt', 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line + '\n')
            print(line)  # Also print to console

if __name__ == "__main__":
    asyncio.run(run_test())
