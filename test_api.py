import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("--- API DIAGNOSTIC ---")
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment variables.")
    exit(1)

print(f"API Key found: {api_key[:5]}...{api_key[-4:]}")

genai.configure(api_key=api_key)

print("\n--- TESTING MODEL ACCESS ---")
try:
    print("Attempting to list models...")
    models = [m.name for m in genai.list_models()]
    print(f"Available models: {models}")
except Exception as e:
    print(f"ERROR Listing Models: {e}")

print("\n--- TESTING GENERATION (gemini-1.5-flash) ---")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, are you working?")
    print(f"Response received: {response.text}")
except Exception as e:
    print(f"ERROR Generating Content: {e}")

print("\n--- TESTING GENERATION (gemini-pro) ---")
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello, are you working?")
    print(f"Response received: {response.text}")
except Exception as e:
    print(f"ERROR Generating Content: {e}")
