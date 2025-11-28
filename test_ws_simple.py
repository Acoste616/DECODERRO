import asyncio
import websockets

async def test_ws():
    uri = "ws://localhost:8000/ws/analysis/test-session"
    print(f"[WS] Attempting to connect to {uri}...")
    try:
        async with websockets.connect(uri, timeout=10) as websocket:
            print("[WS] Connected successfully!")
            print("[WS] Waiting for messages...")
            # Send a keepalive ping
            await websocket.send("ping")
            # Wait for any response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"[WS] Received: {response}")
    except asyncio.TimeoutError:
        print("[ERROR] Timeout while connecting or receiving")
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ws())
