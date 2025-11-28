import os
from dotenv import load_dotenv
from ollama import Client

load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")

print(f"Testing Ollama Cloud...")
print(f"URL: {OLLAMA_BASE_URL}")
print(f"Key: {OLLAMA_API_KEY[:20]}...")

try:
    client = Client(
        host=OLLAMA_BASE_URL,
        headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
    )
    
    # Test simple chat
    print("\n📝 Testing chat with deepseek-v3.1:671b...")
    response = client.chat(
        model='deepseek-v3.1:671b',
        messages=[
            {'role': 'user', 'content': 'Say "test successful" in JSON format: {"result": "..."}'}
        ],
        stream=False
    )
    
    print(f"✅ Response received!")
    print(f"Content: {response['message']['content'][:200]}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
