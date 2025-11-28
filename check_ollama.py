import requests
import json
import sys

def check_ollama():
    base_url = "http://localhost:11434"
    print(f"Checking Ollama at {base_url}...")
    
    # Check tags
    try:
        resp = requests.get(f"{base_url}/api/tags")
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            print(f"✅ Ollama is UP. Found {len(models)} models.")
            for m in models:
                print(f" - {m['name']}")
            
            # Check for deepseek-chat or similar
            target_model = "deepseek-chat"
            if not any(m['name'].startswith("deepseek") for m in models):
                print("⚠️ 'deepseek' model not found! Slow Path requires a deep model.")
            else:
                print(f"✅ 'deepseek' model found.")
        else:
            print(f"❌ Ollama returned status {resp.status_code}")
    except Exception as e:
        print(f"❌ Could not connect to Ollama: {e}")
        return

if __name__ == "__main__":
    check_ollama()
