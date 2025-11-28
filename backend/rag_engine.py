"""
ULTRA v3.1 Recovery - Real RAG Engine
Uses local sentence-transformers (all-MiniLM-L6-v2) for zero-cost embeddings
"""
import os
import asyncio
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "ultra_knowledge"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 produces 384-dimensional vectors

# Initialize Embedding Model (Local)
print(f"[RAG] Loading embedding model: {EMBEDDING_MODEL}...")
try:
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"[RAG] OK - Embedding model loaded successfully")
except Exception as e:
    print(f"[RAG] ERROR - Failed to load embedding model: {e}")
    embedding_model = None

# Initialize Qdrant Client
try:
    print(f"[RAG] Connecting to Qdrant at {QDRANT_URL}...")
    qdrant_client = QdrantClient(url=QDRANT_URL)
    
    # Check if collection exists
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        print(f"[RAG] OK - Connected to collection '{COLLECTION_NAME}'")
    except Exception:
        print(f"[RAG] WARN - Collection '{COLLECTION_NAME}' not found (will be created during ingestion)")
        qdrant_client = None  # Don't create collection here - ingestion script will do it
        
except Exception as e:
    print(f"[RAG] ERROR - Failed to connect to Qdrant: {e}")
    qdrant_client = None


class RAGEngine:
    """Real RAG Engine with local embeddings and Qdrant vector search"""
    
    def __init__(self):
        self.client = qdrant_client
        self.model = embedding_model
        self.collection = COLLECTION_NAME
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using local model"""
        if not self.model:
            return [0.0] * VECTOR_SIZE
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"[RAG] ERROR - Embedding error: {e}")
            return [0.0] * VECTOR_SIZE
    
    async def _get_embedding_async(self, text: str) -> List[float]:
        """Async version using executor to avoid blocking"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_embedding, text)
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Synchronous search"""
        if not self.client or not self.model:
            print("[RAG] WARN - RAG engine not available (using empty results)")
            return []
        
        try:
            vector = self._get_embedding(query)
            hits = self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=limit,
                score_threshold=0.5  # Minimum similarity score
            )
            
            results = []
            for hit in hits:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    **hit.payload  # Unpack all payload fields
                })
            
            print(f"[RAG] OK - Found {len(results)} relevant nuggets")
            return results
            
        except Exception as e:
            print(f"[RAG] ERROR - Search error: {e}")
            return []
    
    async def search_async(self, query: str, limit: int = 5, timeout: float = 1.5) -> List[Dict[str, Any]]:
        """Async search with timeout"""
        if not self.client or not self.model:
            print("[RAG] WARN - RAG engine not available")
            return []
        
        try:
            # Wrap search in timeout
            result = await asyncio.wait_for(
                self._search_internal(query, limit),
                timeout=timeout
            )
            return result
        
        except asyncio.TimeoutError:
            print(f"[RAG] WARN - Search timeout ({timeout}s)")
            return []
        except Exception as e:
            print(f"[RAG] ERROR - Async search error: {e}")
            return []
    
    async def _search_internal(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Internal async search logic"""
        # 1. Generate embedding (async)
        vector = await self._get_embedding_async(query)
        
        # 2. Search Qdrant (wrap sync call in executor)
        loop = asyncio.get_event_loop()
        hits = await loop.run_in_executor(
            None,
            lambda: self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=limit,
                score_threshold=0.5
            )
        )
        
        # 3. Format results
        results = []
        for hit in hits:
            results.append({
                "id": hit.id,
                "score": hit.score,
                **hit.payload
            })
        
        print(f"[RAG] OK - Found {len(results)} nuggets")
        return results


# Global instance
rag_engine = RAGEngine()
