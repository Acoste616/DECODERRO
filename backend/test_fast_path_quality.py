"""
Test Fast Path Quality Improvements
Validates that Prompt 1 and Prompt 2 now receive full session history
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_fast_path_with_context():
    print("="*60)
    print("Testing Fast Path Quality Improvements")
    print("="*60)
    
    # Step 1: Create new session
    print("\n1. Creating new session...")
    response = requests.post(f"{BASE_URL}/sessions/new")
    data = response.json()
    session_id = data["data"]["session_id"]
    print(f"   ✓ Session created: {session_id}")
    
    # Step 2: Send first message
    print("\n2. Sending first message (establishing context)...")
    payload1 = {
        "session_id": session_id,
        "user_input": "Klient pyta o cenę Modelu 3. Wydaje się zainteresowany oszczędnościami.",
        "journey_stage": "Odkrywanie",
        "language": "pl"
    }
    response = requests.post(f"{BASE_URL}/sessions/send", json=payload1)
    result1 = response.json()
    
    if result1["status"] == "success":
        print(f"   ✓ First response: {result1['data']['suggested_response'][:80]}...")
        print(f"   ✓ Questions generated: {len(result1['data']['suggested_questions'])}")
    else:
        print(f"   ✗ Failed: {result1.get('message', 'Unknown error')}")
        return
    
    # Step 3: Send second message (should reference first message context)
    print("\n3. Sending second message (testing context awareness)...")
    payload2 = {
        "session_id": session_id,
        "user_input": "Klient wspomniał, że jeździ 30 000 km rocznie. Ma obawy o zasięg zimą.",
        "journey_stage": "Odkrywanie",
        "language": "pl"
    }
    response = requests.post(f"{BASE_URL}/sessions/send", json=payload2)
    result2 = response.json()
    
    if result2["status"] == "success":
        response_text = result2['data']['suggested_response']
        questions = result2['data']['suggested_questions']
        
        print(f"\n   📊 QUALITY CHECK:")
        print(f"   Response: {response_text[:150]}...")
        
        # Check if response references previous context
        context_indicators = [
            "oszczędności" in response_text.lower(),
            "cena" in response_text.lower() or "koszt" in response_text.lower(),
            "30" in response_text or "km" in response_text
        ]
        
        print(f"\n   Context Awareness Indicators:")
        print(f"   - References savings/cost: {'✓' if context_indicators[0] or context_indicators[1] else '✗'}")
        print(f"   - Mentions mileage context: {'✓' if context_indicators[2] else '✗'}")
        
        print(f"\n   Suggested Questions:")
        for i, q in enumerate(questions, 1):
            print(f"   {i}. {q}")
        
        # Check if questions avoid repetition
        first_questions = result1['data']['suggested_questions']
        question_similarity = sum(1 for q in questions if any(word in q.lower() for fq in first_questions for word in fq.lower().split()[:3]))
        
        print(f"\n   Question Quality:")
        print(f"   - Avoids repetition: {'✓' if question_similarity < 2 else '⚠ Some overlap detected'}")
        
        print(f"\n   {'='*60}")
        print(f"   ✅ FAST PATH QUALITY TEST COMPLETE")
        print(f"   {'='*60}")
        
    else:
        print(f"   ✗ Failed: {result2.get('message', 'Unknown error')}")

if __name__ == "__main__":
    try:
        test_fast_path_with_context()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
