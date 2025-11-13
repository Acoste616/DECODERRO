#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for Fast Path quality after RAG import
"""
import requests
import json

API_URL = "http://localhost:8000"

# Test questions
test_questions = [
    "Jaki zasięg ma Model 3 Long Range?",
    "Czy mogę dostać dopłaty do zakupu Tesli?",
    "Jakie są koszty serwisu Tesli?",
    "Czy Tesla ma autopilot?",
]

print("=" * 70)
print("FAST PATH QUALITY TEST")
print("=" * 70)
print()

# Create test session
print("Creating test session...")
response = requests.post(f"{API_URL}/api/v1/sessions/new")
session_data = response.json()

# Try different possible keys
if "session_id" in session_data:
    session_id = session_data["session_id"]
elif "data" in session_data and "session_id" in session_data["data"]:
    session_id = session_data["data"]["session_id"]
elif "id" in session_data:
    session_id = session_data["id"]
else:
    print(f"ERROR: Could not find session_id in response")
    print(f"Response: {json.dumps(session_data, indent=2, ensure_ascii=False)}")
    exit(1)

print(f"Session created: {session_id}")
print()

# Test each question
for idx, question in enumerate(test_questions, 1):
    print(f"TEST {idx}: {question}")
    print("-" * 70)

    try:
        response = requests.post(
            f"{API_URL}/api/v1/sessions/send",
            json={
                "session_id": session_id,
                "user_input": question,
                "journey_stage": "Odkrywanie",
                "language": "pl"
            }
        )

        if response.status_code == 200:
            result = response.json()

            print(f"Full Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
            print()
            print(f"Response Type: {result.get('response_type', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 'N/A')}")
            print(f"Response Preview: {result.get('suggested_response', '')[:200]}...")

            # Check if response contains specific knowledge
            response_text = result.get('suggested_response', '').lower()
            has_specific_info = any(keyword in response_text for keyword in [
                'km', 'wltp', 'kwh', 'złot', 'zł', 'rok', 'tesla', 'model'
            ])

            if has_specific_info:
                print("[OK] Response contains specific knowledge")
            else:
                print("[WARN] Response seems generic")
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"[ERROR] Exception: {e}")

    print()

print("=" * 70)
print("TEST COMPLETED")
print("=" * 70)
