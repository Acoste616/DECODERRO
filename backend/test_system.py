#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA v3.0 - System Test Script
================================
Comprehensive test of all system components
"""
import sys
import io
import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient

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

QDRANT_HOST = 'localhost'
QDRANT_PORT = 6333
QDRANT_COLLECTION = 'ultra_rag_v1'

print("=" * 70)
print("ULTRA v3.0 - SYSTEM TEST")
print("=" * 70)
print()

# =============================================================================
# TEST 1: PostgreSQL Connection
# =============================================================================
print("TEST 1: PostgreSQL Connection")
print("-" * 70)
try:
    db_conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)
    print("✅ PostgreSQL connected successfully")

    # Check tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"✅ Found {len(tables)} tables:")
    for table in tables:
        print(f"   - {table['table_name']}")

    cursor.close()
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    db_conn = None

print()

# =============================================================================
# TEST 2: Sessions Table
# =============================================================================
if db_conn:
    print("TEST 2: Sessions Table")
    print("-" * 70)
    try:
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)

        # Count total sessions
        cursor.execute("SELECT COUNT(*) as count FROM sessions")
        total = cursor.fetchone()['count']
        print(f"✅ Total sessions: {total}")

        # Get recent sessions
        cursor.execute("""
            SELECT session_id, status, created_at, ended_at
            FROM sessions
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()

        if recent:
            print(f"✅ Recent sessions:")
            for s in recent:
                status = s['status'] or 'active'
                print(f"   - {s['session_id']} | {status} | {s['created_at']}")
        else:
            print("⚠️  No sessions found")

        cursor.close()
    except Exception as e:
        print(f"❌ Sessions test failed: {e}")

print()

# =============================================================================
# TEST 3: Conversation Logs
# =============================================================================
if db_conn:
    print("TEST 3: Conversation Logs")
    print("-" * 70)
    try:
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)

        # Count total messages
        cursor.execute("SELECT COUNT(*) as count FROM conversation_log")
        total = cursor.fetchone()['count']
        print(f"✅ Total messages: {total}")

        # Count by role
        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM conversation_log
            GROUP BY role
        """)
        by_role = cursor.fetchall()
        for row in by_role:
            print(f"   - {row['role']}: {row['count']}")

        cursor.close()
    except Exception as e:
        print(f"❌ Conversation logs test failed: {e}")

print()

# =============================================================================
# TEST 4: Feedback System
# =============================================================================
if db_conn:
    print("TEST 4: Feedback System (Łapki)")
    print("-" * 70)
    try:
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)

        # Count feedback
        cursor.execute("SELECT COUNT(*) as count FROM feedback_logs")
        total = cursor.fetchone()['count']
        print(f"✅ Total feedback entries: {total}")

        # Count by type
        cursor.execute("""
            SELECT feedback_type, COUNT(*) as count
            FROM feedback_logs
            GROUP BY feedback_type
        """)
        by_type = cursor.fetchall()

        if by_type:
            print("✅ Feedback breakdown:")
            for row in by_type:
                emoji = "👍" if row['feedback_type'] == 'up' else "👎"
                print(f"   {emoji} {row['feedback_type']}: {row['count']}")
        else:
            print("⚠️  No feedback found (system not tested yet)")

        # Get recent feedback with context
        cursor.execute("""
            SELECT
                f.feedback_id,
                f.session_id,
                f.feedback_type,
                f.feedback_note,
                f.created_at
            FROM feedback_logs f
            ORDER BY f.created_at DESC
            LIMIT 3
        """)
        recent = cursor.fetchall()

        if recent:
            print(f"✅ Recent feedback:")
            for f in recent:
                emoji = "👍" if f['feedback_type'] == 'up' else "👎"
                note = f['feedback_note'][:50] if f['feedback_note'] else 'No comment'
                print(f"   {emoji} {f['session_id'][:8]}... | {note}...")

        cursor.close()
    except Exception as e:
        print(f"❌ Feedback test failed: {e}")

print()

# =============================================================================
# TEST 5: Slow Path Logs
# =============================================================================
if db_conn:
    print("TEST 5: Slow Path (Opus Magnum) Logs")
    print("-" * 70)
    try:
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)

        # Count slow path executions
        cursor.execute("SELECT COUNT(*) as count FROM slow_path_logs")
        total = cursor.fetchone()['count']
        print(f"✅ Total Slow Path executions: {total}")

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM slow_path_logs
            GROUP BY status
        """)
        by_status = cursor.fetchall()

        if by_status:
            print("✅ Execution status:")
            for row in by_status:
                emoji = "✅" if row['status'] == 'Success' else "❌"
                print(f"   {emoji} {row['status']}: {row['count']}")
        else:
            print("⚠️  No Slow Path executions found")

        # Get recent executions
        cursor.execute("""
            SELECT
                session_id,
                status,
                timestamp,
                json_output->>'suggested_stage' as suggested_stage
            FROM slow_path_logs
            ORDER BY timestamp DESC
            LIMIT 3
        """)
        recent = cursor.fetchall()

        if recent:
            print(f"✅ Recent executions:")
            for s in recent:
                stage = s['suggested_stage'] or 'N/A'
                print(f"   - {s['session_id'][:8]}... | {s['status']} | Stage: {stage}")

        cursor.close()
    except Exception as e:
        print(f"❌ Slow Path test failed: {e}")

print()

# =============================================================================
# TEST 6: Golden Standards
# =============================================================================
if db_conn:
    print("TEST 6: Golden Standards")
    print("-" * 70)
    try:
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)

        # Count golden standards
        cursor.execute("SELECT COUNT(*) as count FROM golden_standards")
        total = cursor.fetchone()['count']
        print(f"✅ Total golden standards: {total}")

        if total > 0:
            # Sample standards
            cursor.execute("""
                SELECT
                    trigger_context,
                    LENGTH(golden_response) as response_length,
                    language
                FROM golden_standards
                ORDER BY created_at DESC
                LIMIT 3
            """)
            samples = cursor.fetchall()

            print(f"✅ Sample standards:")
            for s in samples:
                trigger = s['trigger_context'][:50]
                print(f"   - [{s['language']}] {trigger}... ({s['response_length']} chars)")
        else:
            print("⚠️  No golden standards defined yet")

        cursor.close()
    except Exception as e:
        print(f"❌ Golden standards test failed: {e}")

print()

# =============================================================================
# TEST 7: Qdrant Vector Database
# =============================================================================
print("TEST 7: Qdrant Vector Database (RAG)")
print("-" * 70)
try:
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Get collections
    collections = qdrant.get_collections()
    print(f"✅ Qdrant connected! Collections: {len(collections.collections)}")

    # Check main collection
    try:
        collection_info = qdrant.get_collection(QDRANT_COLLECTION)
        print(f"✅ Collection '{QDRANT_COLLECTION}' found:")
        print(f"   - Points (nuggets): {collection_info.points_count}")
        print(f"   - Vectors: {collection_info.vectors_count}")

        # Sample nuggets
        if collection_info.points_count > 0:
            points = qdrant.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=5,
                with_payload=True,
                with_vectors=False
            )[0]

            print(f"✅ Sample nuggets:")
            for p in points:
                title = p.payload.get('title', 'No title')[:60]
                ntype = p.payload.get('type', 'general')
                lang = p.payload.get('language', '?')
                print(f"   - [{lang}] [{ntype}] {title}...")
        else:
            print("⚠️  No RAG nuggets in database - use bulk import to add!")

    except Exception as e:
        print(f"❌ Collection not found or error: {e}")
        print("   → Run backend initialization to create collection")

except Exception as e:
    print(f"❌ Qdrant connection failed: {e}")

print()

# =============================================================================
# SUMMARY
# =============================================================================
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)

if db_conn:
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)

    # Get counts
    cursor.execute("SELECT COUNT(*) as c FROM sessions")
    sessions_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) as c FROM conversation_log")
    messages_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) as c FROM feedback_logs")
    feedback_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) as c FROM slow_path_logs")
    slow_path_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) as c FROM golden_standards")
    golden_count = cursor.fetchone()['c']

    print(f"📊 Database Statistics:")
    print(f"   - Sessions: {sessions_count}")
    print(f"   - Messages: {messages_count}")
    print(f"   - Feedback: {feedback_count}")
    print(f"   - Slow Path executions: {slow_path_count}")
    print(f"   - Golden standards: {golden_count}")
    print()

    # System health check
    all_working = True

    if sessions_count == 0:
        print("⚠️  WARNING: No sessions found - system not tested yet")
        all_working = False

    if feedback_count == 0:
        print("⚠️  WARNING: No feedback - thumbs up/down not tested")
        all_working = False

    if slow_path_count == 0:
        print("⚠️  WARNING: No Slow Path executions - Opus Magnum not tested")
        all_working = False

    if all_working:
        print("✅ All systems operational and tested!")
    else:
        print("⚠️  Some features not tested yet - try using the system")

    cursor.close()
    db_conn.close()

print()
print("=" * 70)
print("Test completed!")
print("=" * 70)
