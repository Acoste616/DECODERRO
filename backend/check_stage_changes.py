#!/usr/bin/env python3
import psycopg2
import json

conn = psycopg2.connect(
    user='postgres',
    password='postgres',
    host='localhost',
    port='5432',
    database='ultra_db'
)

cur = conn.cursor()

# Check sessions where AI changed the stage
cur.execute("""
    SELECT session_id,
           json_output->>'suggested_stage' as stage,
           json_output->>'overall_confidence' as conf
    FROM slow_path_logs
    WHERE json_output->>'suggested_stage' IS NOT NULL
      AND json_output->>'suggested_stage' != 'Odkrywanie'
      AND json_output->>'suggested_stage' != 'Discovery'
    ORDER BY timestamp DESC
    LIMIT 5
""")

rows = cur.fetchall()

print("\n" + "="*70)
print("SESJE GDZIE AI ZMIENIL ETAP:")
print("="*70)

if rows:
    for row in rows:
        print(f"\nSession: {row[0]}")
        print(f"  Suggested Stage: {row[1]}")
        print(f"  Confidence: {row[2]}%")
else:
    print("\nBrak sesji gdzie AI zmienił etap z 'Odkrywanie'")

# Show all unique stages suggested by AI
cur.execute("""
    SELECT DISTINCT json_output->>'suggested_stage' as stage, COUNT(*) as count
    FROM slow_path_logs
    WHERE json_output->>'suggested_stage' IS NOT NULL
    GROUP BY json_output->>'suggested_stage'
    ORDER BY count DESC
""")

print("\n" + "="*70)
print("STATYSTYKA ETAPÓW SUGEROWANYCH PRZEZ AI:")
print("="*70)
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} sesji")

cur.close()
conn.close()
