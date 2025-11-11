"""
Test Slow Path functionality and error handling
Validates DeepSeek 671B integration via Ollama Cloud
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_slow_path_integration():
    print("="*60)
    print("Testing Slow Path Integration & Error Handling")
    print("="*60)
    
    # Step 1: Create session
    print("\n1. Creating new session...")
    response = requests.post(f"{BASE_URL}/sessions/new")
    data = response.json()
    
    if data["status"] != "success":
        print(f"   ✗ Failed to create session: {data.get('message')}")
        return
    
    session_id = data["data"]["session_id"]
    print(f"   ✓ Session created: {session_id}")
    
    # Step 2: Send message to trigger Slow Path
    print("\n2. Sending message to trigger Slow Path analysis...")
    payload = {
        "session_id": session_id,
        "user_input": "Klient jest bardzo zainteresowany Modelem Y. Pyta o TCO, program Mój Elektryk oraz koszty eksploatacji. Ma firmę B2B i ma obawy o zasięg zimą.",
        "journey_stage": "Analiza",
        "language": "pl"
    }
    
    response = requests.post(f"{BASE_URL}/sessions/send", json=payload)
    result = response.json()
    
    if result["status"] != "success":
        print(f"   ✗ Failed: {result.get('message')}")
        return
    
    print(f"   ✓ Fast Path response received")
    print(f"   Response: {result['data']['suggested_response'][:100]}...")
    
    # Step 3: Wait for Slow Path to complete (via background task)
    print("\n3. Waiting for Slow Path analysis...")
    print("   (This triggers asynchronously - check backend logs)")
    print("   Expected flow:")
    print("   - Backend fetches session history")
    print("   - Calls Ollama Cloud API")
    print("   - Processes Opus Magnum JSON")
    print("   - Sends via WebSocket (if connected)")
    
    # Step 4: Check backend logs for Slow Path execution
    print("\n4. MANUAL CHECK REQUIRED:")
    print("   Please verify in backend terminal logs:")
    print("   - '🧠 Starting Slow Path for...' message")
    print("   - '🤖 Calling Ollama Cloud for...' message")
    print("   - Either success: '✓ Slow Path complete' OR")
    print("   - Error handling: '❌ CRITICAL SLOW PATH ERROR'")
    print("   - Error should NOT crash server!")
    
    print(f"\n{'='*60}")
    print("Test Complete - Check Backend Logs")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        test_slow_path_integration()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
