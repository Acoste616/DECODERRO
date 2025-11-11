import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"

response = requests.get(url)
data = response.json()

print("Available Gemini models:")
for model in data.get("models", [])[:10]:
    name = model.get("name", "")
    supported = model.get("supportedGenerationMethods", [])
    if "generateContent" in supported:
        print(f"  ✓ {name}")
