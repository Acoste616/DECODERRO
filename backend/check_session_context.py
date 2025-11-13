#!/usr/bin/env python3
import psycopg2
import json
import sys

conn = psycopg2.connect(
    user='postgres',
    password='postgres',
    host='localhost',
    port='5432',
    database='ultra_db'
)

cur = conn.cursor()

# Get session where AI changed to "Analiza"
session_id = "S-QAF-316"

print("\n" + "="*70)
print(f"ANALIZA SESJI: {session_id}")
print("="*70)

# Get conversation history
cur.execute("""
    SELECT role, content, timestamp
    FROM conversation_log
    WHERE session_id = %s
    ORDER BY timestamp ASC
""", (session_id,))

print("\nHISTORIA KONWERSACJI:")
print("-"*70)
for idx, row in enumerate(cur.fetchall(), 1):
    print(f"\n{idx}. [{row[0]}]")
    print(f"   {row[1][:200]}...")

# Get AI analysis
cur.execute("""
    SELECT json_output->>'suggested_stage' as stage,
           json_output->'modules'->'dna_client'->>'holistic_summary' as summary,
           json_output->'modules'->'deep_motivation'->>'key_insight' as insight
    FROM slow_path_logs
    WHERE session_id = %s
    ORDER BY timestamp DESC
    LIMIT 1
""", (session_id,))

row = cur.fetchone()
if row:
    print("\n" + "="*70)
    print("ANALIZA AI:")
    print("="*70)
    print(f"\nSuggested Stage: {row[0]}")
    print(f"\nHolistic Summary:\n  {row[1][:300] if row[1] else 'N/A'}...")
    print(f"\nKey Insight:\n  {row[2][:300] if row[2] else 'N/A'}...")

# Check for "rodzina" mentions
cur.execute("""
    SELECT json_output->'modules'->'decision_vectors'->'vectors' as vectors
    FROM slow_path_logs
    WHERE session_id = %s
    ORDER BY timestamp DESC
    LIMIT 1
""", (session_id,))

row = cur.fetchone()
if row and row[0]:
    vectors = json.loads(row[0]) if isinstance(row[0], str) else row[0]
    print("\n" + "="*70)
    print("DECISION VECTORS (czy AI wspomina o rodzinie?):")
    print("="*70)
    for vector in vectors:
        if 'rodzina' in str(vector).lower() or 'family' in str(vector).lower():
            print(f"\n  UWAGA: Znaleziono wzmiankę o rodzinie!")
            print(f"  Stakeholder: {vector.get('stakeholder', 'N/A')}")
            print(f"  Strategy: {vector.get('strategy', 'N/A')[:100]}...")

cur.close()
conn.close()
