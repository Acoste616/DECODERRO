#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA v4.0 - Direct Database Import (Tesla-Gotham Enhanced)
=============================================================
Imports data directly to PostgreSQL and Qdrant
Bypasses HTTP endpoints

ENHANCED (v4.0): Now supports importing from datatoupload/ folder

Usage:
    python direct_import.py                     # Import from default locations
    python direct_import.py --datatoupload      # Import from datatoupload/ folder
    python direct_import.py --folder <path>     # Import from custom folder

Requirements:
    - sentence-transformers (for embeddings)
    - psycopg2 (PostgreSQL driver)
    - qdrant_client (vector database client)
"""
import json
import sys
import io
import uuid
import glob
import argparse
from datetime import datetime, timezone
from pathlib import Path
import psycopg2
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load environment
load_dotenv()

# Parse arguments
parser = argparse.ArgumentParser(description='Import RAG nuggets and Golden Standards to databases')
parser.add_argument('--datatoupload', action='store_true', help='Import from datatoupload/ folder')
parser.add_argument('--folder', type=str, help='Custom folder path to import from')
args = parser.parse_args()

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
print("ULTRA v4.0 - DIRECT DATABASE IMPORT (Tesla-Gotham Enhanced)")
print("=" * 70)
print()

# Connect to databases
print("Connecting to databases...")
try:
    db_conn = psycopg2.connect(**POSTGRES_CONFIG)
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print("✅ Connected to PostgreSQL and Qdrant")
except Exception as e:
    print(f"❌ Failed to connect to databases: {e}")
    print("Make sure PostgreSQL and Qdrant are running.")
    sys.exit(1)
print()


def import_nugget(nugget: dict, idx: int) -> bool:
    """Import a single RAG nugget to Qdrant."""
    try:
        # Handle both formats: {"title", "content"} and {"trigger_context", "content"}
        title = nugget.get("title", nugget.get("trigger_context", "Untitled"))
        content = nugget.get("content", nugget.get("golden_response", ""))

        if not content:
            return False

        # Generate embedding using SentenceTransformer
        content_to_embed = f"{title} {content}"
        embedding = embedding_model.encode(content_to_embed).tolist()

        # Create point for Qdrant
        point_id = str(uuid.uuid4())
        payload = {
            "title": title[:200],  # Truncate long titles
            "content": content,
            "type": nugget.get("type", nugget.get("category", "general")),
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
        return True

    except Exception as e:
        print(f"   ⚠️ Error at nugget {idx+1}: {e}")
        return False


def import_golden_standard(standard: dict, idx: int, cursor) -> bool:
    """Import a single golden standard to PostgreSQL and Qdrant."""
    try:
        trigger = standard.get("trigger_context", "")
        response = standard.get("golden_response", standard.get("content", ""))
        tags = standard.get("tags", [])

        if not trigger or not response:
            return False

        # Insert into PostgreSQL (skip if duplicate)
        cursor.execute(
            """
            INSERT INTO golden_standards
            (trigger_context, golden_response, tags, language, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (trigger_context, language) DO NOTHING
            """,
            (
                trigger,
                response,
                tags,
                "pl",
                datetime.now(timezone.utc)
            )
        )

        # Generate embedding for Qdrant using SentenceTransformer
        embedding_content = f"{trigger} {response}"
        embedding = embedding_model.encode(embedding_content).tolist()

        # Add to Qdrant
        point_id = str(uuid.uuid4())
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[models.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "title": f"Golden: {trigger[:50]}...",
                    "content": response,
                    "type": "golden_standard",
                    "tags": tags,
                    "language": "pl",
                    "trigger_context": trigger,
                    "category": standard.get("category", "general"),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            )]
        )
        return True

    except Exception as e:
        print(f"   ⚠️ Error at standard {idx+1}: {e}")
        return False


def import_from_datatoupload():
    """Import all JSON files from datatoupload/ folder."""
    print("IMPORTING FROM datatoupload/ FOLDER")
    print("-" * 70)

    # Find datatoupload folder
    base_path = Path(__file__).parent.parent / "datatoupload"

    if not base_path.exists():
        print(f"❌ Folder not found: {base_path}")
        return

    print(f"📂 Source folder: {base_path}")

    # Find all JSON files
    json_files = list(base_path.glob("*.json"))
    print(f"   Found {len(json_files)} JSON files")

    if not json_files:
        print("   No JSON files to import.")
        return

    # Separate nugget files and golden standard files
    nugget_files = [f for f in json_files if "nugget" in f.name.lower()]
    golden_files = [f for f in json_files if "gol" in f.name.lower()]
    other_files = [f for f in json_files if f not in nugget_files and f not in golden_files]

    print(f"   📄 Nugget files: {len(nugget_files)}")
    print(f"   📄 Golden standard files: {len(golden_files)}")
    print(f"   📄 Other files: {len(other_files)}")
    print()

    # Import nuggets
    if nugget_files:
        print("STEP 1: Importing RAG Nuggets from datatoupload/")
        print("-" * 70)

        total_success = 0
        total_errors = 0

        for file_path in nugget_files:
            print(f"\n   📄 Processing: {file_path.name}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle both array and single object formats
                if isinstance(data, list):
                    nuggets = data
                else:
                    nuggets = [data]

                success_count = 0
                for idx, nugget in enumerate(nuggets):
                    if import_nugget(nugget, idx):
                        success_count += 1

                print(f"      ✅ Imported {success_count}/{len(nuggets)} nuggets")
                total_success += success_count
                total_errors += len(nuggets) - success_count

            except Exception as e:
                print(f"      ❌ Error loading file: {e}")
                total_errors += 1

        print(f"\n✅ Nuggets import completed! Total: {total_success} success, {total_errors} errors")

    # Import golden standards
    if golden_files:
        print("\nSTEP 2: Importing Golden Standards from datatoupload/")
        print("-" * 70)

        cursor = db_conn.cursor()
        total_success = 0
        total_errors = 0

        for file_path in golden_files:
            print(f"\n   📄 Processing: {file_path.name}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle both array and single object formats
                if isinstance(data, list):
                    standards = data
                else:
                    standards = [data]

                success_count = 0
                for idx, standard in enumerate(standards):
                    if import_golden_standard(standard, idx, cursor):
                        success_count += 1

                print(f"      ✅ Imported {success_count}/{len(standards)} golden standards")
                total_success += success_count
                total_errors += len(standards) - success_count

            except Exception as e:
                print(f"      ❌ Error loading file: {e}")
                total_errors += 1

        db_conn.commit()
        cursor.close()
        print(f"\n✅ Golden standards import completed! Total: {total_success} success, {total_errors} errors")

    # Handle other files (try to detect format)
    if other_files:
        print("\nSTEP 3: Processing other JSON files")
        print("-" * 70)

        cursor = db_conn.cursor()

        for file_path in other_files:
            print(f"\n   📄 Processing: {file_path.name}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    items = data
                else:
                    items = [data]

                # Detect format by first item
                if items:
                    first_item = items[0]
                    if "trigger_context" in first_item and "golden_response" in first_item:
                        # Golden standard format
                        for idx, item in enumerate(items):
                            import_golden_standard(item, idx, cursor)
                        print(f"      ✅ Imported as golden standards")
                    elif "title" in first_item or "content" in first_item:
                        # Nugget format
                        for idx, item in enumerate(items):
                            import_nugget(item, idx)
                        print(f"      ✅ Imported as nuggets")
                    else:
                        print(f"      ⚠️ Unknown format, skipping")

            except Exception as e:
                print(f"      ❌ Error: {e}")

        db_conn.commit()
        cursor.close()


def import_from_default_locations():
    """Import from default file locations (../rag_nuggets_final.json, etc.)"""

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

        for idx, nugget in enumerate(nuggets):
            if import_nugget(nugget, idx):
                success_count += 1
            else:
                error_count += 1

            if (idx + 1) % 50 == 0:
                print(f"   Progress: {idx + 1}/{len(nuggets)} ({success_count} success, {error_count} errors)")

        print(f"\n✅ RAG Nuggets import completed!")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")

    except FileNotFoundError:
        print("⚠️ ../rag_nuggets_final.json not found, skipping...")
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

        for idx, standard in enumerate(standards):
            if import_golden_standard(standard, idx, cursor):
                success_count += 1
            else:
                error_count += 1

            if (idx + 1) % 50 == 0:
                print(f"   Progress: {idx + 1}/{len(standards)} ({success_count} success, {error_count} errors)")

        # Commit all database changes
        db_conn.commit()
        cursor.close()

        print(f"\n✅ Golden Standards import completed!")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")

    except FileNotFoundError:
        print("⚠️ ../golden_standards_final.json not found, skipping...")
    except Exception as e:
        print(f"❌ Error: {e}")
        db_conn.rollback()


# Main execution
if args.datatoupload or args.folder:
    import_from_datatoupload()
else:
    import_from_default_locations()

print()

# Close connections
db_conn.close()

print("=" * 70)
print("IMPORT COMPLETED!")
print("=" * 70)
print()
print("Run 'python test_system.py' to verify the import")
print()
print("TIP: Use 'python direct_import.py --datatoupload' to import from datatoupload/ folder")
