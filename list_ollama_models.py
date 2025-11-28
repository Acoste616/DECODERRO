import os
from ollama import Client
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OLLAMA_API_KEY")
base_url = os.getenv("OLLAMA_BASE_URL")

print(f"Connecting to {base_url} with key {api_key[:10]}...")

try:
    client = Client(
        host=base_url,
        headers={'Authorization': f'Bearer {api_key}'}
    )
    
    # Try to list models if the client supports it, or just try to chat with a likely name
    # The python library might not have a 'list' method for cloud yet, or it's 'list()'
    try:
        models = client.list()
        print("Available Models:")
        for m in models['models']:
            print(f"- {m['name']}")
    except Exception as e:
        print(f"Could not list models: {e}")
        
except Exception as e:
    print(f"Error: {e}")
