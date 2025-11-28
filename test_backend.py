import requests
import json

url = "http://localhost:8000/api/chat"
payload = {
    "session_id": "test-1",
    "user_input": "Klient pyta o cenę Model 3",
    "journey_stage": "DISCOVERY",
    "language": "PL",
    "history": []
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
