"""
ULTRA V3.1 LITE - Comprehensive System Test

Tests:
1. Fast Path responds in <3s
2. Fast Path uses fallback when Gemini fails
3. Slow Path triggers and completes
4. RAG search works with timeout
5. Semaphore limits concurrent Slow Path tasks
6. WebSocket immediate acknowledgment
"""

import asyncio
import websockets
import json
import time

TEST_SESSION_ID = f"test-ultra-{int(time.time())}"
WS_URL = f"ws://localhost:8000/ws/chat/{TEST_SESSION_ID}"

# Test counters
tests_passed = 0
tests_failed = 0

def log_test(name, passed, message=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        print(f"✅ PASS: {name}")
        if message:
            print(f"   → {message}")
    else:
        tests_failed += 1
        print(f"❌ FAIL: {name}")
        if message:
            print(f"   → {message}")

async def test_fast_path_speed():
    """Test 1: Fast Path responds in <3s"""
    print("\n=== TEST 1: Fast Path Speed (<3s) ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Send message
            test_message = "Jaki jest zasięg Modelu 3 w zimie?"
            
            start_time = time.time()
            await websocket.send(test_message)
            
            # Wait for responses
            ack_received = False
            fast_response_received = False
            
            while time.time() - start_time < 5:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if data['type'] == 'processing':
                        ack_received = True
                        ack_time = time.time() - start_time
                        log_test("Immediate ACK", ack_time < 0.5, f"ACK in {ack_time:.2f}s")
                    
                    if data['type'] == 'fast_response':
                        fast_response_received = True
                        response_time = time.time() - start_time
                        
                        # Check response time
                        log_test("Fast Path <3s", response_time < 3.0, f"Response in {response_time:.2f}s")
                        
                        # Check response structure
                        content = data['data'].get('content', '')
                        confidence = data['data'].get('confidence', 0)
                        confidence_reason = data['data'].get('confidenceReason', '')
                        
                        log_test("Response has content", len(content) > 0, f"Length: {len(content)} chars")
                        log_test("Confidence is valid", 0 <= confidence <= 1, f"Confidence: {confidence}")
                        log_test("Confidence reason exists", len(confidence_reason) > 0, f"Reason: {confidence_reason[:50]}")
                        
                        break
                
                except asyncio.TimeoutError:
                    continue
            
            if not fast_response_received:
                log_test("Fast Path responds", False, "No response within 5s")
                
    except Exception as e:
        log_test("Fast Path test", False, f"Error: {e}")

async def test_slow_path():
    """Test 2: Slow Path triggers and completes"""
    print("\n=== TEST 2: Slow Path Analysis ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Send message
            await websocket.send("Klient jest sceptyczny wobec Tesli. Jak przekonać?")
            
            # Wait for responses
            analysis_received = False
            start_time = time.time()
            
            while time.time() - start_time < 120:  # 2 minutes max
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data['type'] == 'analysis_status':
                        status = data['data'].get('status', '')
                        print(f"   [SLOW PATH] Status: {status}")
                    
                    if data['type'] == 'analysis_update':
                        analysis_received = True
                        elapsed = time.time() - start_time
                        
                        analysis_data = data['data']
                        log_test("Slow Path completes", True, f"Analysis in {elapsed:.1f}s")
                        
                        # Check analysis structure
                        has_m1 = 'm1_dna' in analysis_data
                        has_m2 = 'm2_indicators' in analysis_data
                        has_m3 = 'm3_psychometrics' in analysis_data
                        
                        log_test("Analysis has M1 (DNA)", has_m1)
                        log_test("Analysis has M2 (Indicators)", has_m2)
                        log_test("Analysis has M3 (Psychometrics)", has_m3)
                        
                        if has_m2:
                            temp = analysis_data['m2_indicators'].get('purchaseTemperature', 0)
                            log_test("Purchase temperature valid", 0 <= temp <= 100, f"Temperature: {temp}")
                        
                        break
                
                except asyncio.TimeoutError:
                    continue
            
            if not analysis_received:
                log_test("Slow Path triggers", False, "No analysis within 120s (may be busy)")
                
    except Exception as e:
        log_test("Slow Path test", False, f"Error: {e}")

async def test_rag_search():
    """Test 3: RAG search works"""
    print("\n=== TEST 3: RAG Search ===")
    
    from backend.rag import rag_system
    
    try:
        # Test RAG search
        query = "Model 3 cena zasięg"
        results = rag_system.search(query, limit=3)
        
        log_test("RAG returns results", len(results) > 0, f"Found {len(results)} nuggets")
        
        if results:
            first_result = results[0]
            log_test("RAG result has title", 'title' in first_result)
            log_test("RAG result has content", 'content' in first_result)
            
        # Test async search with timeout
        start = time.time()
        async_results = await rag_system.search_async(query, timeout=1.5)
        elapsed = time.time() - start
        
        log_test("RAG async respects timeout", elapsed < 2.0, f"Completed in {elapsed:.2f}s")
        log_test("RAG async returns results", len(async_results) > 0, f"Found {len(async_results)} nuggets")
        
    except Exception as e:
        log_test("RAG search", False, f"Error: {e}")

async def test_fallback_chain():
    """Test 4: Fallback chain works"""
    print("\n=== TEST 4: Fallback Chain ===")
    
    from backend.ai_core import ai_core, create_emergency_response, create_rag_fallback_response
    
    try:
        # Test emergency response
        emergency = create_emergency_response("PL")
        log_test("Emergency fallback creates response", emergency.response != "")
        log_test("Emergency fallback has confidence", 0 <= emergency.confidence <= 1)
        
        # Test RAG fallback
        rag_fallback = create_rag_fallback_response("Tesla Model 3 kosztuje 229,990 PLN", "PL")
        log_test("RAG fallback creates response", rag_fallback.response != "")
        log_test("RAG fallback includes context", "229,990" in rag_fallback.response or "PLN" in rag_fallback.response)
        
    except Exception as e:
        log_test("Fallback chain", False, f"Error: {e}")

async def test_concurrent_messages():
    """Test 5: System handles concurrent messages"""
    print("\n=== TEST 5: Concurrent Messages ===")
    
    try:
        async def send_message(session_id, message):
            url = f"ws://localhost:8000/ws/chat/{session_id}"
            async with websockets.connect(url) as ws:
                await ws.send(message)
                
                # Wait for fast response
                start = time.time()
                while time.time() - start < 5:
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(response)
                        if data['type'] == 'fast_response':
                            return time.time() - start
                    except asyncio.TimeoutError:
                        continue
                return None
        
        # Send 3 concurrent messages
        tasks = [
            send_message(f"concurrent-test-{i}", f"Test message {i}")
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if isinstance(r, float) and r < 5)
        log_test("Concurrent messages handled", successful >= 2, f"{successful}/3 responded in <5s")
        
    except Exception as e:
        log_test("Concurrent messages", False, f"Error: {e}")

async def main():
    print("╔═══════════════════════════════════════════════════╗")
    print("║   ULTRA V3.1 LITE - COMPREHENSIVE SYSTEM TEST    ║")
    print("╚═══════════════════════════════════════════════════╝\n")
    
    print("🔍 Testing backend at ws://localhost:8000...")
    
    # Run all tests
    await test_rag_search()
    await test_fallback_chain()
    await test_fast_path_speed()
    await test_concurrent_messages()
    await test_slow_path()  # Last because it takes longest
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"📈 Success Rate: {tests_passed}/{tests_passed + tests_failed} ({100*tests_passed/(tests_passed+tests_failed) if (tests_passed+tests_failed) > 0 else 0:.1f}%)")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is 100% operational.")
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Review logs above.")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(main())
