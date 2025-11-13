#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA v3.0 - Final Data Import Script
======================================
Imports rag_nuggets_final.json and golden_standards_final.json
Removes 'id' field and calls bulk import endpoints
"""
import json
import requests
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_BASE = "http://localhost:8000/api/v1/admin"
ADMIN_KEY = "ULTRA_DOJO_KEY_8a4f9b2c_qoder_ai_2025"
LANGUAGE = "pl"

print("=" * 70)
print("ULTRA v3.0 - FINAL DATA IMPORT")
print("=" * 70)
print()

# =============================================================================
# Import RAG Nuggets
# =============================================================================
print("STEP 1: Importing RAG Nuggets")
print("-" * 70)

try:
    # Load file
    with open('../rag_nuggets_final.json', 'r', encoding='utf-8') as f:
        nuggets = json.load(f)

    print(f"✅ Loaded {len(nuggets)} nuggets from file")

    # Remove 'id' field from each nugget
    cleaned_nuggets = []
    for nugget in nuggets:
        cleaned = {k: v for k, v in nugget.items() if k != 'id'}
        cleaned_nuggets.append(cleaned)

    print(f"✅ Cleaned nuggets (removed 'id' field)")

    # Call bulk import API
    response = requests.post(
        f"{API_BASE}/rag/bulk-import",
        headers={
            "Content-Type": "application/json",
            "X-Admin-Key": ADMIN_KEY
        },
        json={
            "nuggets": cleaned_nuggets,
            "language": LANGUAGE
        },
        timeout=300  # 5 minutes timeout for large import
    )

    print(f"   HTTP Status: {response.status_code}")
    result = response.json()
    print(f"   Response keys: {result.keys() if isinstance(result, dict) else type(result)}")

    if result.get('status') in ['success', 'partial']:
        print(f"✅ Import completed!")
        print(f"   Success: {result['data']['success_count']}")
        print(f"   Errors: {result['data']['error_count']}")

        if result['data']['errors']:
            print(f"\n⚠️  First 5 errors:")
            for error in result['data']['errors'][:5]:
                print(f"   - {error}")
    else:
        print(f"❌ Import failed: {result.get('message', 'Unknown error')}")

except FileNotFoundError:
    print("❌ File not found: rag_nuggets_final.json")
    print("   Make sure the file is in the project root directory")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# =============================================================================
# Import Golden Standards
# =============================================================================
print("STEP 2: Importing Golden Standards")
print("-" * 70)

try:
    # Load file
    with open('../golden_standards_final.json', 'r', encoding='utf-8') as f:
        standards = json.load(f)

    print(f"✅ Loaded {len(standards)} golden standards from file")

    # Remove 'id' field from each standard
    cleaned_standards = []
    for standard in standards:
        cleaned = {k: v for k, v in standard.items() if k != 'id'}
        cleaned_standards.append(cleaned)

    print(f"✅ Cleaned standards (removed 'id' field)")

    # Call bulk import API
    response = requests.post(
        f"{API_BASE}/golden-standards/bulk-import",
        headers={
            "Content-Type": "application/json",
            "X-Admin-Key": ADMIN_KEY
        },
        json={
            "standards": cleaned_standards,
            "language": LANGUAGE
        },
        timeout=300  # 5 minutes timeout for large import
    )

    print(f"   HTTP Status: {response.status_code}")
    result = response.json()
    print(f"   Response keys: {result.keys() if isinstance(result, dict) else type(result)}")

    if result.get('status') in ['success', 'partial']:
        print(f"✅ Import completed!")
        print(f"   Success: {result['data']['success_count']}")
        print(f"   Errors: {result['data']['error_count']}")

        if result['data']['errors']:
            print(f"\n⚠️  First 5 errors:")
            for error in result['data']['errors'][:5]:
                print(f"   - {error}")
    else:
        print(f"❌ Import failed: {result.get('message', 'Unknown error')}")

except FileNotFoundError:
    print("❌ File not found: golden_standards_final.json")
    print("   Make sure the file is in the project root directory")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 70)
print("IMPORT COMPLETED!")
print("=" * 70)
print()
print("Next steps:")
print("1. Run: python test_system.py")
print("2. Check the new counts in database")
print("3. Test RAG retrieval in the UI")
print()
