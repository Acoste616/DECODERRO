import asyncio
import os
from ollama import AsyncClient
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = "https://ollama.com"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

async def test_ollama_lib():
    print(f"Testing with ollama library...")
    print(f"Host: {OLLAMA_BASE_URL}")
    print(f"API Key present: {bool(OLLAMA_API_KEY)}")
    
    client = AsyncClient(
        host=OLLAMA_BASE_URL,
        headers={'Authorization': 'Bearer ' + OLLAMA_API_KEY}
    )
    
    try:
        print("\n1. Listing models...")
        response = await client.list()
        models = response.get('models', [])
        print(f"Found {len(models)} models:")
        for m in models:
            print(f" - {m.get('name')}")
            
        # Try to find deepseek
        deepseek_models = [m.get('name') for m in models if 'deepseek' in m.get('name').lower()]
        if deepseek_models:
            print(f"\nFound DeepSeek models: {deepseek_models}")
            target_model = deepseek_models[0]
        else:
            print("\nNo DeepSeek models found, trying 'deepseek-r1' anyway...")
            target_model = "deepseek-r1"
            
        print(f"\n2. Testing chat with {target_model}...")
        message = {'role': 'user', 'content': 'Hello!'}
        
        response = await client.chat(model=target_model, messages=[message])
        print(f"Success! Response: {response['message']['content']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_lib())
