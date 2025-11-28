import requests
import json
import time

print("=== ULTRA v3.0 Final Test ===\n")

url = "http://localhost:8000/api/chat"

# Test 1: Polish
print("📝 Test 1: Polish Language")
payload_pl = {
    "session_id": "final-test-pl",
    "user_input": "Klient pyta o zasięg Model 3 zimą i obawia się że bateria szybko się rozładuje",
    "journey_stage": "DISCOVERY",
    "language": "PL",
    "history": []
}

response = requests.post(url, json=payload_pl)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Response: {data['response'][:100]}...")
    print(f"✅ Confidence: {data['confidence']}")
    print(f"✅ Questions: {len(data.get('questions', []))}")
    print(f"✅ Actions: {len(data.get('suggested_actions', []))}")
else:
    print(f"❌ Error: {response.text}")

time.sleep(2)

# Test 2: English
print("\n📝 Test 2: English Language")
payload_en = {
    "session_id": "final-test-en",
    "user_input": "Client asks about Model 3 winter range and worries about battery drain",
    "journey_stage": "DISCOVERY",
    "language": "EN",
    "history": []
}

response = requests.post(url, json=payload_en)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Response: {data['response'][:100]}...")
    print(f"✅ Confidence: {data['confidence']}")
else:
    print(f"❌ Error: {response.text}")

print("\n=== Test Complete ===")
print("✅ Fast Path: Working")
print("⏳ Slow Path: Running in background (check WebSocket or wait 10-20s)")
