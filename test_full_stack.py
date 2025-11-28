"""
ULTRA v3.1 - Full Stack Verification Test
Tests: RAG → Gemini Fast Path → DeepSeek Slow Path
"""
import asyncio
import websockets
import json
import sys

TEST_SESSION_ID = "TEST_SESSION_001"
WEBSOCKET_URL = f"ws://localhost:8000/ws/chat/{TEST_SESSION_ID}"

# The complex test scenario
TEST_MESSAGE = """Klient mówi, że Tesla Model Y jest za droga w porównaniu do Audi Q4. Jest analityczny, pyta o konkretne koszty serwisu i utratę wartości. Wydaje się sceptyczny co do jakości wykonania."""

async def run_full_stack_test():
    print("=" * 80)
    print("ULTRA v3.1 - FULL STACK VERIFICATION TEST")
    print("=" * 80)
    print("\n🎯 TEST SCENARIO:")
    print(f"   Session: {TEST_SESSION_ID}")
    print(f"   Message: {TEST_MESSAGE}")
    print("\n📡 Connecting to WebSocket...")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ Connected!")
            
            # Send test message
            print(f"\n📤 Sending message...")
            await websocket.send(json.dumps({"content": TEST_MESSAGE}))
            print("✅ Message sent")
            
            print("\n⏳ Waiting for responses...")
            print("=" * 80)
            
            # Collect responses
            response_count = 0
            max_wait = 120  # 2 minutes max
            fast_response_received = False
            analysis_received = False
            
            while response_count < 10 and (not fast_response_received or not analysis_received):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=max_wait)
                    data = json.loads(message)
                    response_count += 1
                    
                    msg_type = data.get("type", "unknown")
                    
                    if msg_type == "processing":
                        print("\n[1/3] 🔄 PROCESSING...")
                    
                    elif msg_type == "fast_response":
                        fast_response_received = True
                        print("\n[2/3] ⚡ FAST PATH RESPONSE RECEIVED")
                        print("=" * 80)
                        
                        response_data = data.get("data", {})
                        content = response_data.get("content", "")
                        confidence = response_data.get("confidence", 0)
                        confidence_reason = response_data.get("confidenceReason", "")
                        suggested_actions = response_data.get("suggestedActions", [])
                        
                        print(f"\n📊 CONFIDENCE: {confidence:.0%}")
                        print(f"\n💭 STRATEGY:")
                        print(f"   {confidence_reason}")
                        
                        print(f"\n💬 GEMINI RESPONSE:")
                        print("-" * 80)
                        print(content)
                        print("-" * 80)
                        
                        if suggested_actions:
                            print(f"\n🎯 SUGGESTED ACTIONS:")
                            for i, action in enumerate(suggested_actions, 1):
                                print(f"   {i}. {action}")
                        
                        print("\n✅ Fast Path Complete")
                        print("\n⏳ Waiting for Slow Path analysis...")
                    
                    elif msg_type == "analysis_status":
                        status_data = data.get("data", {})
                        status = status_data.get("status", "")
                        if status == "analyzing":
                            print("\n[3/3] 🧠 SLOW PATH ANALYZING...")
                    
                    elif msg_type == "analysis_update":
                        analysis_received = True
                        print("\n[3/3] 🎉 SLOW PATH ANALYSIS RECEIVED")
                        print("=" * 80)
                        
                        analysis_data = data.get("data", {})
                        
                        # Summary
                        summary = analysis_data.get("summary", "N/A")
                        print(f"\n📝 EXECUTIVE SUMMARY:")
                        print(f"   {summary}")
                        
                        # Psychometrics
                        psycho = analysis_data.get("psychometrics", {})
                        if psycho:
                            print(f"\n🧠 PSYCHOMETRIC PROFILE:")
                            print(f"   DISC Type: {psycho.get('disc_type', '?')} ({psycho.get('disc_confidence', 0)}% confidence)")
                            print(f"   Motivation: {psycho.get('main_motivation', '?')}")
                            print(f"   Communication: {psycho.get('communication_style', '?')}")
                            print(f"   Emotional State: {psycho.get('emotional_state', '?')}")
                        
                        # Sales Metrics
                        metrics = analysis_data.get("sales_metrics", {})
                        if metrics:
                            print(f"\n📊 SALES METRICS:")
                            print(f"   Purchase Probability: {metrics.get('purchase_probability', 0)}%")
                            print(f"   Temperature: {metrics.get('sales_temperature', '?')}")
                            objections = metrics.get("objections", [])
                            if objections:
                                print(f"   Objections: {', '.join(objections[:3])}")
                        
                        # Next Move
                        next_move = analysis_data.get("next_move", {})
                        if next_move:
                            print(f"\n🎯 STRATEGIC RECOMMENDATION:")
                            print(f"   {next_move.get('strategic_advice', 'N/A')}")
                            print(f"   Tactic: {next_move.get('recommended_tactic', '?')}")
                        
                        # Journey Stage
                        journey = analysis_data.get("journey_stage", {})
                        if journey:
                            print(f"\n🗺️ JOURNEY STAGE:")
                            print(f"   {journey.get('current_stage', '?')} ({journey.get('confidence', 0)}% confidence)")
                        
                        print("\n✅ Slow Path Complete")
                        break  # Got everything we need
                    
                    elif msg_type == "analysis_error":
                        print(f"\n⚠️ Analysis Error: {data.get('data', {}).get('error', 'Unknown')}")
                
                except asyncio.TimeoutError:
                    print(f"\n⚠️ Timeout after {max_wait}s")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    break
            
            print("\n" + "=" * 80)
            print("TEST COMPLETE")
            print("=" * 80)
            
            print("\n📋 VERIFICATION CHECKLIST:")
            print(f"   [{'✅' if fast_response_received else '❌'}] Fast Path response received")
            print(f"   [{'✅' if analysis_received else '❌'}] Slow Path analysis received")
            
            if fast_response_received and analysis_received:
                print("\n🎉 SUCCESS: Full stack is operational!")
            elif fast_response_received:
                print("\n⚠️ PARTIAL: Fast Path works, Slow Path may have issues")
            else:
                print("\n❌ FAILURE: System not responding correctly")
            
            print("\n💡 CHECK BACKEND LOGS FOR:")
            print("   1. [RAG] nugget retrieval")
            print("   2. [FAST PATH] Gemini response")
            print("   3. [ANALYSIS ENGINE] DeepSeek analysis")
    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"\n❌ WebSocket connection failed: {e}")
        print("   Is the server running on port 8000?")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔬 Starting Full Stack Verification Test...\n")
    asyncio.run(run_full_stack_test())
