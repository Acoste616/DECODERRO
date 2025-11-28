import asyncio
import websockets
import sys
import httpx

async def test_ws():
    # 1. Create Session
    async with httpx.AsyncClient() as client:
        print("Creating session...")
        try:
            resp = await client.post("http://localhost:8000/api/sessions")
            if resp.status_code != 200:
                print(f"Failed to create session: {resp.status_code} {resp.text}")
                return
            session_data = resp.json()
            session_id = session_data["id"]
            print(f"Created session: {session_id}")
        except Exception as e:
            print(f"Error creating session: {e}")
            return

    # 2. Connect WS
    uri = f"ws://localhost:8000/ws/chat/{session_id}"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            await websocket.send("Hello")
            print("Sent message")
            
            # Expect Fast Response
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Failed with status code: {e.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
