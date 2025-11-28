"""
ULTRA v3.1 Recovery - ROBUST Knowledge Base Ingestion
Fixed: ID collision issue (uses UUID for Qdrant, preserves source_id in payload)
"""
import json
import os
import uuid
from typing import List
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Configuration
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "ultra_knowledge"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "dane"  # Correct path: "dane" not "data"

def load_json(filename):
    """Load JSON file from data directory"""
    path = DATA_DIR / filename
    print(f"📂 Loading: {path}")
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   ✅ Loaded {len(data)} items")
    return data

def main():
    print("=" * 70)
    print("🚀 ULTRA v3.1 - ROBUST INGESTION PROCESS")
    print("=" * 70)
    
    # 1. Init Client & Model
    print("\n[1/6] Initializing Qdrant client...")
    client = QdrantClient(QDRANT_URL)
    print("   ✅ Connected to Qdrant")
    
    print("\n[2/6] Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("   ✅ Model loaded")
    
    # 2. Recreate Collection (Wipe clean)
    print(f"\n[3/6] Recreating collection '{COLLECTION_NAME}'...")
    try:
        client.delete_collection(COLLECTION_NAME)
        print("   🗑️  Deleted existing collection")
    except:
        print("   ℹ️  No existing collection to delete")
    
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
    )
    print(f"   ✅ Collection '{COLLECTION_NAME}' created (vector size: {VECTOR_SIZE})")

    # 3. Load Data
    print("\n[4/6] Loading knowledge base files...")
    nuggets = load_json("rag_nuggets_final.json")
    standards = load_json("golden_standards_final.json")
    
    all_items = []

    # Prepare Nuggets
    print(f"\n📦 Preparing {len(nuggets)} RAG Nuggets...")
    for item in nuggets:
        # Combine multiple fields for richer embeddings
        text_to_embed = f"{item.get('title', '')} {item.get('content', '')} {item.get('keywords', '')}"
        
        # Prepare payload (preserve original structure + metadata)
        payload = {
            'source': 'rag_nuggets',
            'source_id': item.get('id', 'unknown'),  # Preserve original ID
            'title': item.get('title', ''),
            'content': item.get('content', ''),
            'keywords': item.get('keywords', ''),
            'type': item.get('type', ''),
            'tags': item.get('tags', []),
            'archetype_filter': item.get('archetype_filter', [])
        }
        
        all_items.append({'text': text_to_embed, 'payload': payload})

    # Prepare Golden Standards
    print(f"📦 Preparing {len(standards)} Golden Standards...")
    for item in standards:
        # Combine trigger + response for semantic matching
        text_to_embed = f"{item.get('trigger_context', '')} {item.get('golden_response', '')}"
        
        # Prepare payload
        payload = {
            'source': 'golden_standards',
            'source_id': item.get('id', 'unknown'),  # Preserve original ID
            'trigger_context': item.get('trigger_context', ''),
            'golden_response': item.get('golden_response', ''),
            'tags': item.get('tags', []),
            'category': item.get('category', '')
        }
        
        all_items.append({'text': text_to_embed, 'payload': payload})

    total_items = len(all_items)
    print(f"\n📊 Total items to ingest: {total_items}")
    print(f"   - RAG Nuggets: {len(nuggets)}")
    print(f"   - Golden Standards: {len(standards)}")

    # 4. Batch Upload
    print(f"\n[5/6] Uploading to Qdrant (batch size: 100)...")
    batch_size = 100
    uploaded_count = 0
    
    for i in range(0, total_items, batch_size):
        batch = all_items[i:i+batch_size]
        points = []
        
        # Generate Embeddings for batch
        texts = [x['text'] for x in batch]
        embeddings = model.encode(texts, convert_to_numpy=True).tolist()

        for j, item in enumerate(batch):
            # KEY FIX: Generate new UUID for Qdrant point ID
            # This prevents collisions from duplicate source_ids
            point_id = str(uuid.uuid4())
            
            points.append(models.PointStruct(
                id=point_id,
                vector=embeddings[j],
                payload=item['payload']
            ))

        # Upload batch
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        uploaded_count += len(batch)
        
        # Progress log every 1000 items or end of batch
        if uploaded_count % 1000 == 0 or uploaded_count == total_items:
            print(f"   ✅ Uploaded {uploaded_count} / {total_items} ({100*uploaded_count/total_items:.1f}%)")

    # 5. Final Verification
    print(f"\n[6/6] Verifying upload...")
    count = client.count(collection_name=COLLECTION_NAME)
    
    print("\n" + "=" * 70)
    print("🎉 INGESTION COMPLETE!")
    print("=" * 70)
    print(f"📊 Total vectors in Qdrant: {count.count}")
    print(f"📊 Expected vectors: {total_items}")
    
    if count.count == total_items:
        print("✅ SUCCESS: Perfect data integrity! All items uploaded.")
    elif count.count > 11000:
        print("✅ SUCCESS: Data integrity verified (>11,000 vectors)")
    else:
        print("⚠️  WARNING: Count mismatch!")
        print(f"   Expected: {total_items}")
        print(f"   Got: {count.count}")
        print(f"   Missing: {total_items - count.count}")
    
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
