#!/usr/bin/env python3
import requests
import json

# Create session
resp = requests.post("http://localhost:8000/api/v1/sessions/new")
session_id = resp.json()["session_id"]
print(f"Session: {session_id}")

# Test query
resp = requests.post(
    "http://localhost:8000/api/v1/sessions/send",
    json={
        "session_id": session_id,
        "user_input": "Jaki zasieg ma Model 3 Long Range?",
        "journey_stage": "Odkrywanie",
        "language": "pl"
    }
)

result = resp.json()
print("\nResponse:")
print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
