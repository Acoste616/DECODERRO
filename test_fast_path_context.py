"""
ULTRA v3.0 - Fast Path Context Test

Test to verify that Fast Path receives complete conversation history
after fixing the db.refresh() bug.
"""
import asyncio
import json
import websockets

async def test_multi_message_context():
    """
    Test że Fast Path ma dostęp do pełnej historii przy wielu wiadomościach.
    """
    session_id = f"TEST-CTX-{int(asyncio.get_event_loop().time())}"
    
    print(f"🧪 Testing Fast Path context with session: {session_id}\n")
    
    messages_sent = 0
    responses = []
    
    try:
        async with websockets.connect(f"ws://localhost:8000/ws/chat/{session_id}") as ws:
            test_messages = [
                "Ile kosztuje Model 3?",
                "A z dotacją Mój Elektryk?",
                "Potrzebuję więcej szczegółów o finansowaniu"
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"📤 Sending message {i}: '{message}'")
                await ws.send(json.dumps({"content": message}))
                messages_sent += 1
                
                # Receive messages until we get fast_response
                while True:
                    try:
                        raw_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(raw_msg)
                        
                        if data.get('type') == 'processing':
                            print(f"   ⏳ Processing...")
                            continue
                            
                        elif data.get('type') == 'fast_response':
                            content = data.get('data', {}).get('content', 'No content')
                            confidence = data.get('data', {}).get('confidence', 0.0)
                            conf_reason = data.get('data', {}).get('confidenceReason', 'N/A')
                            
                            print(f"📥 Response {i}:")
                            print(f"   Content: {content[:150]}...")
                            print(f"   Confidence: {confidence:.2f}")
                            print(f"   Reason: {conf_reason}\n")
                            
                            responses.append({
                                'content': content,
                                'confidence': confidence,
                                'reason': conf_reason
                            })
                            break
                            
                        else:
                            print(f"   ℹ️  Other message type: {data.get('type')}")
                            
                    except asyncio.TimeoutError:
                        print(f"   ⚠️  Timeout waiting for response {i}")
                        break
                
                # Wait between messages
                if i < len(test_messages):
                    await asyncio.sleep(1.0)
            
            # === VERIFICATION ===
            print("=" * 60)
            print("VERIFICATION RESULTS:")
            print("=" * 60)
            
            if len(responses) < messages_sent:
                print(f"⚠️  Only received {len(responses)}/{messages_sent} responses\n")
            
            # Check confidences
            for i, resp in enumerate(responses, 1):
                conf = resp['confidence']
                if conf > 0.6:
                    print(f"✅ Message {i} has good context (confidence: {conf:.2f})")
                else:
                    print(f"❌ Message {i} lacks context (confidence: {conf:.2f})")
            
            # Check contextual awareness
            if len(responses) >= 2:
                content2 = responses[1]['content'].lower()
                has_context = any(x in content2 for x in ['model 3', 'tesla', 'dotacją', 'dotacja', '229', '211'])
                
                if has_context:
                    print("✅ Message 2 shows contextual awareness (references Model 3 pricing)")
                else:
                    print("⚠️  Message 2 may lack context from message 1")
            
            print("\n🎉 Test completed!")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("ULTRA v3.0 - Fast Path Context Verification Test")
    print("=" * 60)
    print()
    asyncio.run(test_multi_message_context())
