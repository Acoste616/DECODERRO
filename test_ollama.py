import httpx
import os
from dotenv import load_dotenv
import json

load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")

print(f"Testing Ollama Cloud API...")
print(f"URL: {OLLAMA_BASE_URL}")
print(f"Key: {OLLAMA_API_KEY[:20]}...")

async def test_ollama():
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Try models endpoint
            response = await client.get(
                f"{OLLAMA_BASE_URL}/api/tags",
                headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"}
            )
            print(f"\n✅ Models endpoint: {response.status_code}")
            if response.status_code == 200:
                models = response.json()
                print(f"Available models: {json.dumps(models, indent=2)[:500]}")
            
            # Test 2: Try chat completion
            response = await client.post(
                f"{OLLAMA_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OLLAMA_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-r1:7b",
                    "messages": [{"role": "user", "content": "Test"}],
                    "max_tokens": 50
                }
            )
            print(f"\n✅ Chat completion: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {json.dumps(response.json(), indent=2)[:300]}")
            else:
                print(f"Error: {response.text[:500]}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

import asyncio
asyncio.run(test_ollama())
