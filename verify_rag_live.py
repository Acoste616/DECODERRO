"""
ULTRA v3.1 - RAG Live Verification Test
Tests the complete pipeline: User Query → Qdrant → Gemini → Response
"""
import asyncio
import websockets
import json
import sys

TEST_SESSION_ID = "test_rag_verification"
WEBSOCKET_URL = f"ws://localhost:8000/ws/chat/{TEST_SESSION_ID}"
TEST_QUERY = "Klient martwi się, że zimą zasięg drastycznie spadnie."

async def test_rag_pipeline():
    print("=" * 70)
    print("ULTRA v3.1 - RAG LIVE VERIFICATION TEST")
    print("=" * 70)
    print(f"\n📡 Connecting to WebSocket: {WEBSOCKET_URL}")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ Connected!")
            
            # Send test query
            print(f"\n📤 Sending query:")
            print(f"   '{TEST_QUERY}'")
            await websocket.send(json.dumps({"content": TEST_QUERY}))
            
            print("\n⏳ Waiting for response...")
            print("-" * 70)
            
            # Receive responses
            responses_received = 0
            max_responses = 5  # processing + fast_response + maybe analysis_update
            
            while responses_received < max_responses:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    responses_received += 1
                    
                    msg_type = data.get("type", "unknown")
                    print(f"\n📥 Response #{responses_received} - Type: {msg_type}")
                    
                    if msg_type == "processing":
                        print("   Status: Processing...")
                    
                    elif msg_type == "fast_response":
                        print("\n" + "=" * 70)
                        print("🚀 FAST PATH RESPONSE RECEIVED")
                        print("=" * 70)
                        
                        response_data = data.get("data", {})
                        
                        # Extract key fields
                        content = response_data.get("content", "")
                        confidence = response_data.get("confidence", 0)
                        confidence_reason = response_data.get("confidenceReason", "")
                        suggested_actions = response_data.get("suggestedActions", [])
                        
                        print(f"\n📊 CONFIDENCE: {confidence:.0%}")
                        print(f"📝 STRATEGY: {confidence_reason}")
                        
                        print(f"\n💬 GEMINI RESPONSE (To Client):")
                        print("-" * 70)
                        print(content)
                        print("-" * 70)
                        
                        if suggested_actions:
                            print(f"\n🎯 SUGGESTED ACTIONS:")
                            for i, action in enumerate(suggested_actions, 1):
                                print(f"   {i}. {action}")
                        
                        # This is the main response we care about
                        print("\n✅ Fast Path complete - breaking loop")
                        break
                    
                    elif msg_type == "analysis_update":
                        print("   (Slow Path analysis - not critical for this test)")
                    
                    elif msg_type == "analysis_status":
                        status = data.get("data", {}).get("status", "")
                        print(f"   Analysis Status: {status}")
                    
                    else:
                        print(f"   Data: {json.dumps(data, indent=2)[:200]}...")
                
                except asyncio.TimeoutError:
                    print("\n⚠️  Timeout waiting for more responses")
                    break
                except json.JSONDecodeError as e:
                    print(f"\n❌ JSON decode error: {e}")
                    print(f"   Raw message: {message[:200]}...")
            
            print("\n" + "=" * 70)
            print("TEST COMPLETE")
            print("=" * 70)
            
            print("\n📋 VERIFICATION CHECKLIST:")
            print("   [ ] Backend logs show: '[RAG] ✅ Found X relevant nuggets from Qdrant'")
            print("   [ ] Response mentions specific winter range numbers (480-520km or similar)")
            print("   [ ] Response references pompa ciepła (heat pump) or preconditioning")
            print("   [ ] Confidence score > 70%")
            
            print("\n💡 TIP: Check backend terminal for RAG retrieval logs!")
            print("   Look for: '[RAG] ✅ Found 4 relevant nuggets from Qdrant'")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\n🔬 Starting RAG verification test...\n")
    asyncio.run(test_rag_pipeline())
