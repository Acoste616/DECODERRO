#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    user='postgres',
    password='postgres',
    host='localhost',
    port='5432',
    database='ultra_db'
)

cursor = conn.cursor()

# Get sessions table schema
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'sessions'
    ORDER BY ordinal_position;
""")

print("SESSIONS TABLE SCHEMA:")
print("=" * 60)
for row in cursor.fetchall():
    print(f"{row[0]:<30} {row[1]:<20} NULL: {row[2]}")

# Check if there's any journey_stage tracking
cursor.execute("""
    SELECT session_id, created_at
    FROM sessions
    ORDER BY created_at DESC
    LIMIT 5;
""")

print("\n\nRECENT SESSIONS:")
print("=" * 60)
for row in cursor.fetchall():
    print(f"{row[0]} - {row[1]}")

cursor.close()
conn.close()
