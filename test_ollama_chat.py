from ollama import Client
import os
from dotenv import load_dotenv
import json

load_dotenv('.env')

OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'https://ollama.com')

print(f"Connecting to Ollama at {OLLAMA_BASE_URL}...")

try:
    client = Client(
        host=OLLAMA_BASE_URL,
        headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
    )

    prompt = """
    You are a test AI. Generate a simple JSON response with this structure:
    {
      "test": "success",
      "message": "This is a test response"
    }
    """

    print("\nSending test message to gpt-oss:20b...")
    response = client.chat(
        model='gpt-oss:20b',
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        stream=False
    )

    print("\nResponse received!")
    print("Response content:")
    print(response['message']['content'])

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
