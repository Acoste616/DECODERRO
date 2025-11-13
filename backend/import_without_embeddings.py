#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA v3.0 - Import Without Embeddings
=======================================
Imports golden standards to PostgreSQL only
RAG nuggets need embeddings so we'll skip them for now
"""
import json
import sys
import io
from datetime import datetime, timezone
import psycopg2

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Database config
POSTGRES_CONFIG = {
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432',
    'database': 'ultra_db'
}

print("=" * 70)
print("ULTRA v3.0 - IMPORT WITHOUT EMBEDDINGS")
print("=" * 70)
print()

# Connect to PostgreSQL
print("Connecting to PostgreSQL...")
db_conn = psycopg2.connect(**POSTGRES_CONFIG)
print("✅ Connected")
print()

# =============================================================================
# Import Golden Standards (NO embeddings needed for PostgreSQL)
# =============================================================================
print("Importing Golden Standards to PostgreSQL...")
print("-" * 70)

try:
    with open('../golden_standards_final.json', 'r', encoding='utf-8') as f:
        standards = json.load(f)

    print(f"✅ Loaded {len(standards)} golden standards from file")

    cursor = db_conn.cursor()
    success_count = 0
    error_count = 0

    for idx, standard in enumerate(standards):
        try:
            # Skip if missing golden_response
            if 'golden_response' not in standard or not standard['golden_response']:
                error_count += 1
                continue

            # Insert into PostgreSQL only
            cursor.execute(
                """
                INSERT INTO golden_standards
                (trigger_context, golden_response, tags, language, category, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (trigger_context, language) DO NOTHING
                """,
                (
                    standard["trigger_context"],
                    standard["golden_response"],
                    standard.get("tags", []),
                    "pl",
                    standard.get("category"),  # can be NULL now
                    datetime.now(timezone.utc)
                )
            )

            # Commit after each insert to avoid rollback on error
            db_conn.commit()

            success_count += 1

            if (idx + 1) % 50 == 0:
                print(f"   Progress: {idx + 1}/{len(standards)} ({success_count} success, {error_count} errors)")

        except Exception as e:
            db_conn.rollback()  # Rollback just this one
            error_count += 1
            if error_count <= 5:
                print(f"   ⚠️ Error at item {idx+1}: {e}")
    cursor.close()

    print(f"\n✅ Golden Standards import completed!")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")

except Exception as e:
    print(f"❌ Error: {e}")
    db_conn.rollback()

print()
db_conn.close()

print("=" * 70)
print("IMPORT COMPLETED!")
print("=" * 70)
print()
print("Golden Standards are now in PostgreSQL.")
print("RAG Nuggets require embeddings - waiting for valid Gemini API key.")
print()
print("Check Admin Panel → Feedback tab to see golden standards")
