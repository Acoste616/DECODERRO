import asyncio
import websockets
import requests
import json
import time

SESSION_ID = "debug-session-4"
API_URL = "http://localhost:8000/api/chat"
WS_URL = f"ws://localhost:8000/ws/analysis/{SESSION_ID}"

async def listen_ws():
    print(f"[WS] Connecting to WebSocket: {WS_URL}")
    async with websockets.connect(WS_URL) as websocket:
        print("[WS] WebSocket Connected! Waiting for messages...")

        # Trigger the chat request AFTER connecting to WS
        # We run this in a separate thread or just make a request here if non-blocking,
        # but for simplicity, we'll assume the request is sent shortly after.
        # Actually, let's print a message telling the user (me) that the listener is ready.

        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=180.0)
                data = json.loads(message)
                print(f"\n[WS] WebSocket Message Received: {data.get('type')}")

                if data.get('type') == 'analysis_update':
                    print("[SUCCESS] Analysis received!")
                    print(json.dumps(data['data'], indent=2)[:500] + "...")
                    return
                elif data.get('type') == 'analysis_error':
                    print(f"[ERROR] Analysis Error: {data.get('message')}")
                    return

        except asyncio.TimeoutError:
            print("[ERROR] Timeout waiting for analysis.")

def trigger_chat():
    print(f"\n[API] Sending Chat Request to {API_URL}...")
    payload = {
        "session_id": SESSION_ID,
        "user_input": "Klient mówi, że bardzo podoba mu się przyspieszenie, ale martwi się o ładowanie w trasie.",
        "journey_stage": "DISCOVERY",
        "language": "PL",
        "history": []
    }
    try:
        response = requests.post(API_URL, json=payload)
        print(f"[API] Chat Response ({response.status_code}):")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"[ERROR] Chat Request Error: {e}")

async def main():
    # Start WS listener in background
    listener_task = asyncio.create_task(listen_ws())
    
    # Wait a bit for WS to connect
    await asyncio.sleep(2)
    
    # Trigger chat
    trigger_chat()
    
    # Wait for listener to finish
    await listener_task

if __name__ == "__main__":
    asyncio.run(main())
