"""
Test script to validate Fast Path and Slow Path AI functionality
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test imports
try:
    import google.generativeai as genai
    print("✓ Google Generative AI imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Google Generative AI: {e}")
    sys.exit(1)

try:
    import requests
    print("✓ Requests imported successfully")
except ImportError as e:
    print(f"✗ Failed to import requests: {e}")
    sys.exit(1)

# Check API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_CLOUD_URL = os.getenv("OLLAMA_CLOUD_URL", "https://ollama.com")
GEMINI_MODEL = "gemini-2.0-flash"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_NAME", "deepseek-v3.1:671b-cloud")

if not GEMINI_API_KEY:
    print("✗ GEMINI_API_KEY not set in .env")
    sys.exit(1)
print(f"✓ GEMINI_API_KEY configured: {GEMINI_API_KEY[:10]}...")

if not OLLAMA_API_KEY:
    print("✗ OLLAMA_API_KEY not set in .env")
    sys.exit(1)
print(f"✓ OLLAMA_API_KEY configured: {OLLAMA_API_KEY[:10]}...")

print(f"\n{'='*60}")
print(f"Testing Fast Path (Gemini {GEMINI_MODEL})")
print(f"{'='*60}")

# Test Gemini Fast Path
try:    
    test_prompt = """You are a world-class Tesla sales ambassador. Generate a simple response.

Respond ONLY in this JSON format:
{ "suggested_response": "Test response from Gemini" }
"""
    
    # Use REST API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "parts": [{"text": test_prompt}]
        }],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 512,
            "responseMimeType": "application/json"
        }
    }
    
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10
    )
    
    response.raise_for_status()
    result = response.json()
    
    # Extract text from response
    text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
    
    # Parse response
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    parsed = json.loads(text)
    print(f"✓ Fast Path SUCCESS")
    print(f"  Response: {parsed.get('suggested_response', 'No response')}")
    
except Exception as e:
    print(f"✗ Fast Path FAILED: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*60}")
print(f"Testing Slow Path (Ollama {OLLAMA_MODEL})")
print(f"{'='*60}")

# Test Ollama Slow Path
try:
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_prompt = """You are a sales analyst. Generate a simple JSON analysis.

Respond ONLY in this JSON format:
{
  "overall_confidence": 85,
  "suggested_stage": "Odkrywanie",
  "test": "Simple test from Ollama"
}
"""
    
    # Try chat endpoint first
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "temperature": 0.3,
        "stream": False,
        "format": "json"
    }
    
    print(f"  Sending request to {OLLAMA_CLOUD_URL}/api/chat")
    response = requests.post(
        f"{OLLAMA_CLOUD_URL}/api/chat",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"  Status code: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✗ Slow Path FAILED: Invalid API Key (401)")
    elif response.status_code == 404:
        print(f"⚠ Chat endpoint not found, trying generate endpoint...")
        
        # Try old generate endpoint
        payload_gen = {
            "model": OLLAMA_MODEL,
            "prompt": test_prompt,
            "temperature": 0.3,
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(
            f"{OLLAMA_CLOUD_URL}/api/generate",
            headers=headers,
            json=payload_gen,
            timeout=30
        )
        
        print(f"  Generate status code: {response.status_code}")
    
    response.raise_for_status()
    result = response.json()
    
    # Parse response
    text = result.get('message', {}).get('content', '')
    if not text:
        text = result.get('response', '')
    
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    parsed = json.loads(text)
    print(f"✓ Slow Path SUCCESS")
    print(f"  Confidence: {parsed.get('overall_confidence', 'N/A')}")
    print(f"  Stage: {parsed.get('suggested_stage', 'N/A')}")
    print(f"  Test: {parsed.get('test', 'N/A')}")
    
except Exception as e:
    print(f"✗ Slow Path FAILED: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*60}")
print("Test Summary")
print(f"{'='*60}")
print("If both tests passed, the AI paths are configured correctly!")
print("If any test failed, check the error messages above.")
