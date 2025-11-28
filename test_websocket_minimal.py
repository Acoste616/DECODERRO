import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat/test-session-123"
    print(f"[TEST] Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[TEST] ✅ Connected successfully!")
            
            # Send a test message
            test_payload = {"content": "Cześć, pytam o Model 3"}
            print(f"[TEST] Sending: {test_payload}")
            await websocket.send(json.dumps(test_payload))
            
            #  Wait for response
            print("[TEST] Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            data = json.loads(response)
            print(f"[TEST] ✅ Received response type: {data.get('type')}")
            print(f"[TEST] Response preview: {str(data)[:200]}...")
            
            return True
    except asyncio.TimeoutError:
        print("[ERROR] ❌ Timeout - no response received")
        return False
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"[ERROR] ❌ WebSocket connection failed: HTTP {e.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_websocket())
