import asyncio
import websockets
import json
import time
import sys

SESSION_ID = f"verify-{int(time.time())}"
WS_URL = f"ws://localhost:8000/ws/chat/{SESSION_ID}"

def log(msg):
    print(msg)
    with open("verify_output.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def verify_fix():
    log(f"[TEST] Connecting to {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as websocket:
            log("[TEST] Connected.")
            
            # Send message
            msg = {
                "content": "Klient pyta o zasięg Modelu 3 w zimie. Jest sceptyczny."
            }
            await websocket.send(json.dumps(msg))
            log(f"[TEST] Sent: {msg['content']}")
            
            fast_passed = False
            slow_passed = False
            
            start_time = time.time()
            
            while True:
                elapsed = time.time() - start_time
                if elapsed > 60:
                    log("[TEST] Timeout waiting for responses (60s).")
                    break
                    
                try:
                    log(f"[TEST] Waiting for message... ({int(elapsed)}s elapsed)")
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    msg_type = data.get("type")
                    
                    log(f"[TEST] Received: {msg_type}")
                    
                    if msg_type == "fast_response":
                        reason = data["data"].get("confidenceReason", "")
                        log(f"[TEST] Confidence Reason: '{reason}'")
                        
                        if "STEP 0" in reason:
                            log("❌ FAIL: Confidence Reason still contains debug info!")
                        elif len(reason) > 100:
                            log("⚠️ WARNING: Confidence Reason is very long.")
                        else:
                            log("✅ PASS: Confidence Reason looks user-friendly.")
                            fast_passed = True
                            
                    elif msg_type == "analysis_update":
                        log("[TEST] Slow Path Analysis received!")
                        slow_passed = True
                        log("✅ PASS: Slow Path triggered and returned data.")
                        break
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    log(f"[TEST] Error receiving: {e}")
                    break
            
            if fast_passed and slow_passed:
                log("\n🎉 ALL TESTS PASSED!")
            else:
                log("\n❌ TESTS FAILED.")
                if not fast_passed: log("- Fast Path failed or timed out")
                if not slow_passed: log("- Slow Path failed or timed out")

    except Exception as e:
        log(f"[TEST] Connection Error: {e}")

if __name__ == "__main__":
    # Clear log file
    with open("verify_output.log", "w") as f: f.write("")
    asyncio.run(verify_fix())
