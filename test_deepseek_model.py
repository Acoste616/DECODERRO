import os
from ollama import Client
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OLLAMA_API_KEY")
base_url = os.getenv("OLLAMA_BASE_URL")

print(f"Testing deepseek-v3.1:671b-cloud model...")

try:
    client = Client(
        host=base_url,
        headers={'Authorization': f'Bearer {api_key}'}
    )
    
    # Try to use deepseek-v3.1:671b-cloud
    response = client.chat(
        model='deepseek-v3.1:671b-cloud',
        messages=[
            {
                'role': 'user',
                'content': 'Hello, please respond with "TEST OK" to confirm you are working.'
            }
        ],
        stream=False
    )
    
    print(f"✅ SUCCESS: deepseek-v3.1:671b-cloud is available!")
    print(f"Response: {response['message']['content']}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"\nTrying to list all available models...")
    try:
        models = client.list()
        print("Available Models:")
        for m in models.get('models', []):
            print(f"- {m.get('name', m)}")
    except:
        pass
