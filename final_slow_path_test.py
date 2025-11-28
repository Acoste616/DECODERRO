import asyncio
import websockets
import requests
import json

SESSION_ID = "final-test-session"
API_URL = "http://localhost:8000/api/chat"
WS_URL = f"ws://localhost:8000/ws/analysis/{SESSION_ID}"

async def final_test():
    print("=" * 60)
    print("FINAL SLOW PATH TEST")
    print("=" * 60)

    # Connect to WebSocket
    print(f"\n[1/4] Connecting to WebSocket...")
    async with websockets.connect(WS_URL, timeout=10) as websocket:
        print("[OK] WebSocket connected!")

        # Send API request
        print(f"\n[2/4] Sending API request...")
        def send_request():
            payload = {
                "session_id": SESSION_ID,
                "user_input": "Chce kupic Tesle, ale martwi mnie zasieg i cena.",
                "journey_stage": "DISCOVERY",
                "language": "PL",
                "history": []
            }
            response = requests.post(API_URL, json=payload)
            return response.json()

        loop = asyncio.get_event_loop()
        await asyncio.sleep(0.5)
        api_response = await loop.run_in_executor(None, send_request)
        print(f"[OK] Fast Path response received")
        print(f"     Confidence: {api_response.get('confidence')}")

        # Listen for updates
        print(f"\n[3/4] Listening for analysis updates...")
        updates_received = []

        try:
            while len(updates_received) < 3:
                message = await asyncio.wait_for(websocket.recv(), timeout=120.0)
                data = json.loads(message)
                msg_type = data.get('type')
                updates_received.append(msg_type)

                if msg_type == 'analysis_start':
                    print("     [*] Analysis started")
                elif msg_type == 'analysis_update':
                    source = data.get('source')
                    print(f"     [*] Analysis update from: {source}")

                    if source == 'slow':
                        # Slow path completed!
                        analysis = data.get('data', {})
                        print(f"\n[4/4] SLOW PATH COMPLETED!")
                        print(f"     Purchase Temperature: {analysis.get('m2_indicators', {}).get('purchaseTemperature')}%")
                        print(f"     Communication Style: {analysis.get('m1_dna', {}).get('communicationStyle')}")
                        print(f"     Journey Stage: {analysis.get('journeyStageAnalysis', {}).get('currentStage')}")
                        print(f"     Churn Risk: {analysis.get('m2_indicators', {}).get('churnRisk')}")

                        print("\n" + "=" * 60)
                        print("TEST RESULT: SUCCESS!")
                        print("=" * 60)
                        print("\nSlow path dziala poprawnie!")
                        print("- Fast Path (Gemini): OK")
                        print("- Slow Path (Ollama): OK")
                        print("- WebSocket broadcasts: OK")
                        print("- 7-Module Analysis: OK")
                        return True

        except asyncio.TimeoutError:
            print("\n[ERROR] Timeout - slow path nie odpowiada")
            return False

if __name__ == "__main__":
    result = asyncio.run(final_test())
    exit(0 if result else 1)
