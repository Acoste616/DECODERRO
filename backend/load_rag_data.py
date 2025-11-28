"""
Load RAG nuggets from dane/rag_nuggets_final.json into Qdrant
"""
import json
import os
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Connect to Qdrant
qdrant = QdrantClient(url="http://localhost:6333")

COLLECTION_NAME = "ultra_rag_v1"

def load_nuggets():
    """Load nuggets from JSON file"""
    nuggets_path = "dane/rag_nuggets_final.json"
    
    if not os.path.exists(nuggets_path):
        print(f"ERROR: {nuggets_path} not found!")
        return []
    
    with open(nuggets_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both formats: array or object with 'nuggets' key
    if isinstance(data, list):
        nuggets = data
    elif isinstance(data, dict) and 'nuggets' in data:
        nuggets = data['nuggets']
    else:
        nuggets = data
    
    print(f"Loaded {len(nuggets)} nuggets from {nuggets_path}")
    return nuggets

def create_collection():
    """Create or recreate Qdrant collection"""
    try:
        qdrant.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    except:
        pass
    
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=768,  # Gemini text-embedding-004 dimension
            distance=Distance.COSINE
        )
    )
    print(f"Created collection: {COLLECTION_NAME}")

def generate_embedding(text: str):
    """Generate embedding using Gemini"""
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']

def index_nuggets(nuggets):
    """Index all nuggets into Qdrant"""
    points = []
    
    for idx, nugget in enumerate(nuggets):
        # Extract fields
        nugget_id = nugget.get('id', f"nugget-{idx}")
        title = nugget.get('title', '')
        content = nugget.get('content', '')
        keywords = nugget.get('keywords', '')
        language = nugget.get('language', 'pl')
        
        # Combine title + content for embedding
        text_to_embed = f"{title}\n{content}"
        
        # Generate embedding
        print(f"Embedding {idx+1}/{len(nuggets)}: {title[:50]}...")
        embedding = generate_embedding(text_to_embed)
        
        # Create point
        point = PointStruct(
            id=nugget_id if isinstance(nugget_id, int) else hash(nugget_id) % (2**63),
            vector=embedding,
            payload={
                "id": nugget_id,
                "title": title,
                "content": content,
                "keywords": keywords,
                "language": language
            }
        )
        points.append(point)
        
        # Batch upload every 50 points
        if len(points) >= 50:
            qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f"  → Uploaded batch ({len(points)} points)")
            points = []
    
    # Upload remaining
    if points:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"  → Uploaded final batch ({len(points)} points)")
    
    print(f"\n✅ Indexed {len(nuggets)} nuggets successfully!")

def verify_collection():
    """Verify collection was created correctly"""
    info = qdrant.get_collection(COLLECTION_NAME)
    print(f"\n📊 Collection Info:")
    print(f"   Name: {COLLECTION_NAME}")
    print(f"   Points: {info.points_count}")
    print(f"   Vectors: 768D (Cosine)")

if __name__ == "__main__":
    print("🚀 ULTRA RAG Data Loader\n")
    
    nuggets = load_nuggets()
    if not nuggets:
        exit(1)
    
    create_collection()
    index_nuggets(nuggets)
    verify_collection()
    
    print("\n✅ RAG data loaded successfully!")
