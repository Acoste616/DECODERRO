#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA v3.0 - Direct Database Import
====================================
Imports data directly to PostgreSQL and Qdrant
Bypasses HTTP endpoints
"""
import json
import sys
import io
import uuid
from datetime import datetime, timezone
import psycopg2
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load environment
load_dotenv()

# Initialize SentenceTransformer (same as main.py)
print("Loading embedding model...")
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("✅ Embedding model loaded")

# Database config
POSTGRES_CONFIG = {
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432',
    'database': 'ultra_db'
}

QDRANT_HOST = 'localhost'
QDRANT_PORT = 6333
QDRANT_COLLECTION = 'ultra_rag_v1'

print("=" * 70)
print("ULTRA v3.0 - DIRECT DATABASE IMPORT")
print("=" * 70)
print()

# Connect to databases
print("Connecting to databases...")
db_conn = psycopg2.connect(**POSTGRES_CONFIG)
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
print("✅ Connected to PostgreSQL and Qdrant")
print()

# =============================================================================
# Import RAG Nuggets
# =============================================================================
print("STEP 1: Importing RAG Nuggets")
print("-" * 70)

try:
    with open('../rag_nuggets_final.json', 'r', encoding='utf-8') as f:
        nuggets = json.load(f)

    print(f"✅ Loaded {len(nuggets)} nuggets from file")

    success_count = 0
    error_count = 0
    errors = []

    for idx, nugget in enumerate(nuggets):
        try:
            # Generate embedding using SentenceTransformer (same as main.py)
            content_to_embed = f"{nugget['title']} {nugget['content']}"
            embedding = embedding_model.encode(content_to_embed).tolist()

            # Create point for Qdrant
            point_id = str(uuid.uuid4())
            payload = {
                "title": nugget["title"],
                "content": nugget["content"],
                "type": nugget.get("type", "general"),
                "tags": nugget.get("tags", []),
                "language": "pl",
                "keywords": nugget.get("keywords", ""),
                "archetype_filter": nugget.get("archetype_filter", []),
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            # Upsert to Qdrant
            qdrant_client.upsert(
                collection_name=QDRANT_COLLECTION,
                points=[models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )]
            )

            success_count += 1

            if (idx + 1) % 50 == 0:
                print(f"   Progress: {idx + 1}/{len(nuggets)} ({success_count} success, {error_count} errors)")

        except Exception as e:
            error_count += 1
            errors.append(f"Item {idx+1}: {str(e)}")
            if len(errors) <= 5:
                print(f"   ⚠️ Error at item {idx+1}: {e}")

    print(f"\n✅ RAG Nuggets import completed!")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")

except Exception as e:
    print(f"❌ Error: {e}")

print()

# =============================================================================
# Import Golden Standards
# =============================================================================
print("STEP 2: Importing Golden Standards")
print("-" * 70)

try:
    with open('../golden_standards_final.json', 'r', encoding='utf-8') as f:
        standards = json.load(f)

    print(f"✅ Loaded {len(standards)} golden standards from file")

    cursor = db_conn.cursor()
    success_count = 0
    error_count = 0
    errors = []

    for idx, standard in enumerate(standards):
        try:
            # Insert into PostgreSQL (skip if duplicate)
            cursor.execute(
                """
                INSERT INTO golden_standards
                (trigger_context, golden_response, tags, language, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (trigger_context, language) DO NOTHING
                """,
                (
                    standard["trigger_context"],
                    standard["golden_response"],
                    standard.get("tags", []),
                    "pl",
                    datetime.now(timezone.utc)
                )
            )

            # Generate embedding for Qdrant using SentenceTransformer
            embedding_content = f"{standard['trigger_context']} {standard['golden_response']}"
            embedding = embedding_model.encode(embedding_content).tolist()

            # Add to Qdrant
            point_id = str(uuid.uuid4())
            qdrant_client.upsert(
                collection_name=QDRANT_COLLECTION,
                points=[models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "title": f"Golden Standard: {standard['trigger_context'][:50]}...",
                        "content": standard["golden_response"],
                        "type": "golden_standard",
                        "tags": standard.get("tags", []),
                        "language": "pl",
                        "trigger_context": standard["trigger_context"],
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                )]
            )

            success_count += 1

            if (idx + 1) % 50 == 0:
                print(f"   Progress: {idx + 1}/{len(standards)} ({success_count} success, {error_count} errors)")

        except Exception as e:
            error_count += 1
            errors.append(f"Item {idx+1}: {str(e)}")
            if len(errors) <= 5:
                print(f"   ⚠️ Error at item {idx+1}: {e}")

    # Commit all database changes
    db_conn.commit()
    cursor.close()

    print(f"\n✅ Golden Standards import completed!")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")

except Exception as e:
    print(f"❌ Error: {e}")
    db_conn.rollback()

print()

# Close connections
db_conn.close()

print("=" * 70)
print("IMPORT COMPLETED!")
print("=" * 70)
print()
print("Run 'python test_system.py' to verify the import")
