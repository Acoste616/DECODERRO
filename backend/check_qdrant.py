#!/usr/bin/env python3
"""Quick script to check Qdrant status"""
import sys
sys.path.insert(0, '.')

from app.main import QDRANT_CLIENT

try:
    collections = QDRANT_CLIENT.get_collections()
    print(f"✅ Qdrant connected! Collections found: {len(collections.collections)}")

    for collection in collections.collections:
        info = QDRANT_CLIENT.get_collection(collection.name)
        print(f"\n📦 Collection: {collection.name}")
        print(f"   Points: {info.points_count}")
        print(f"   Vectors: {info.vectors_count}")

        # Sample a few points
        if info.points_count > 0:
            points = QDRANT_CLIENT.scroll(collection_name=collection.name, limit=3)[0]
            print(f"   Sample entries:")
            for p in points:
                if p.payload:
                    title = p.payload.get('title', 'No title')[:60]
                    print(f"     - {title}...")

except Exception as e:
    print(f"❌ Error connecting to Qdrant: {e}")
