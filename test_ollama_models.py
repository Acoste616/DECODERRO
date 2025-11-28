from ollama import Client
import os
from dotenv import load_dotenv

load_dotenv('.env')

OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'https://ollama.com')

print(f"Connecting to Ollama at {OLLAMA_BASE_URL}...")
print(f"Using API key: {OLLAMA_API_KEY[:20]}..." if OLLAMA_API_KEY else "No API key")

try:
    client = Client(
        host=OLLAMA_BASE_URL,
        headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
    )

    print("\nListing available models...")
    models = client.list()
    print("\nAvailable models:")
    print(models)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
