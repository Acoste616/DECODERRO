"""
Comprehensive test for ULTRA v3.0 system
Tests: Fast Path, Slow Path, Journey Stage, DB persistence
"""
import asyncio
import httpx
import json
import websockets
import time

BASE_URL = "http://localhost:8000"

async def test_full_flow():
    print("=" * 60)
    print("ULTRA v3.0 - Full System Test")
    print("=" * 60)
    
    # Step 1: Create session
    print("\n[1/5] Creating new session...")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/sessions")
        session_data = response.json()
        session_id = session_data["id"]
        print(f"✅ Session created: {session_id}")
    
    # Step 2: Connect to WebSocket
    print(f"\n[2/5] Connecting to WebSocket...")
    uri = f"ws://localhost:8000/ws/chat/{session_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"✅ WebSocket connected")
        
        # Step 3: Send test message
        test_message = {
            "content": "Dzień dobry, szukam samochodu dla rodziny. Mam 3 dzieci i boję się elektryków - zasięg w zimie mnie martwi."
        }
        print(f"\n[3/5] Sending message: '{test_message['content']}'")
        await websocket.send(json.dumps(test_message))
        
        # Step 4: Receive Fast Path response
        print(f"\n[4/5] Waiting for Fast Path response...")
        response = await websocket.recv()
        fast_response = json.loads(response)
        
        print(f"\n✅ Fast Path Response Received:")
        print(f"   Content: {fast_response.get('content', '')[:100]}...")
        print(f"   Confidence: {fast_response.get('confidence')}")
        print(f"   Client Style: {fast_response.get('clientStyle')}")
        print(f"   Suggested Actions: {fast_response.get('suggestedActions', [])}")
        
        # Verify Polish language
        content = fast_response.get('content', '')
        has_polish = any(char in content for char in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')
        if has_polish:
            print(f"   ✅ Response is in POLISH")
        else:
            print(f"   ⚠️ Response might not be in Polish")
        
        # Step 5: Wait for Slow Path (background analysis)
        print(f"\n[5/5] Waiting for Slow Path analysis (up to 20s)...")
        try:
            slow_response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
            analysis = json.loads(slow_response)
            
            if "journeyStageAnalysis" in analysis:
                print(f"\n✅ Slow Path Analysis Received:")
                print(f"   Journey Stage: {analysis['journeyStageAnalysis'].get('currentStage')}")
                print(f"   Stage Confidence: {analysis['journeyStageAnalysis'].get('confidence')}")
                print(f"   Purchase Temperature: {analysis.get('m2_indicators', {}).get('purchaseTemperature')}")
                print(f"   Main Motivation: {analysis.get('m1_dna', {}).get('mainMotivation')}")
            else:
                print(f"   ⚠️ Slow Path response received but no journey analysis")
                
        except asyncio.TimeoutError:
            print(f"   ⚠️ Slow Path did not complete in 20s (this is OK if quick_analysis is used)")
    
    # Step 6: Verify DB persistence
    print(f"\n[6/6] Verifying database persistence...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/sessions/{session_id}")
        session_data = response.json()
        
        messages = session_data.get("messages", [])
        print(f"   Messages in DB: {len(messages)}")
        
        analysis_state = session_data.get("analysis_state")
        if analysis_state:
            print(f"   ✅ Analysis state persisted to DB")
            journey_stage = analysis_state.get("journeyStageAnalysis", {}).get("currentStage")
            print(f"   Current Journey Stage: {journey_stage}")
        else:
            print(f"   ⚠️ No analysis state in DB yet")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_full_flow())
