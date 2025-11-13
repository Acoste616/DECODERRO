#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add journey_stage column to sessions table
"""
import psycopg2
import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 70)
print("DATABASE MIGRATION: Add journey_stage to sessions")
print("=" * 70)
print()

conn = psycopg2.connect(
    user='postgres',
    password='postgres',
    host='localhost',
    port='5432',
    database='ultra_db'
)

cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='sessions' AND column_name='journey_stage';
    """)

    if cursor.fetchone():
        print("Column 'journey_stage' already exists in sessions table")
    else:
        print("Adding 'journey_stage' column to sessions table...")

        # Add journey_stage column with default value 'Odkrywanie'
        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN journey_stage TEXT NOT NULL DEFAULT 'Odkrywanie';
        """)

        # Add check constraint for valid stages
        cursor.execute("""
            ALTER TABLE sessions
            ADD CONSTRAINT sessions_journey_stage_check
            CHECK (journey_stage IN ('Odkrywanie', 'Analiza', 'Decyzja',
                                     'Discovery', 'Analysis', 'Decision'));
        """)

        conn.commit()
        print("OK - Column added successfully!")
        print()

        # Show updated schema
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'sessions'
            ORDER BY ordinal_position;
        """)

        print("Updated sessions table schema:")
        print("-" * 70)
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} {row[1]:<20} Default: {row[2]} NULL: {row[3]}")

        print()
        print("Migration completed successfully!")

except Exception as e:
    print(f"ERROR: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    cursor.close()
    conn.close()

print()
print("=" * 70)
