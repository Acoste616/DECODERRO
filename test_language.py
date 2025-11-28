import requests
import json

url = "http://localhost:8000/api/chat"
payload = {
    "session_id": "test-pl-1",
    "user_input": "Klient pyta o cenę Model 3 Long Range",
    "journey_stage": "DISCOVERY",
    "language": "PL",
    "history": []
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
data = response.json()
print(f"\nResponse PL:")
print(json.dumps(data, indent=2, ensure_ascii=False))

# Test EN
payload["session_id"] = "test-en-1"
payload["language"] = "EN"
payload["user_input"] = "Client asks about Model 3 Long Range price"
response = requests.post(url, json=payload)
print(f"\n\nResponse EN:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
