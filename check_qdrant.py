"""Check Qdrant collection status"""
from qdrant_client import QdrantClient

try:
    client = QdrantClient(url="http://localhost:6333")
    collection = client.get_collection("ultra_knowledge")
    print(f"Collection: ultra_knowledge")
    print(f"Vectors count: {collection.vectors_count}")
    print(f"Points count: {collection.points_count}")
    print(f"Status: {collection.status}")
except Exception as e:
    print(f"Error: {e}")
