"""
Test script to simulate frontend message and debug backend response.
Sends exact same format as frontend: {"content": "..."}
"""

import asyncio
import websockets
import json
import time

async def test_frontend_format():
    session_id = f"debug-frontend-{int(time.time())}"
    url = f"ws://localhost:8000/ws/chat/{session_id}"
    
    print(f"🔍 Testing frontend format")
    print(f"📡 Connecting to: {url}")
    
    async with websockets.connect(url) as ws:
        # Send message in EXACT frontend format
        message = {
            "content": "klient pyta o dopłaty na model 3 lr awd/ chce wiedzieć o ile spada zasięg i jaki jest czas ładowania"
        }
        
        print(f"\n📤 Sending: {json.dumps(message, ensure_ascii=False)}")
        await ws.send(json.dumps(message))
        
        print("\n📥 Waiting for responses...")
        response_count = 0
        start_time = time.time()
        
        while time.time() - start_time < 120:  # 2 minutes
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(response)
                response_count += 1
                
                print(f"\n[{response_count}] Type: {data['type']}")
                
                if data['type'] == 'processing':
                    print(f"   → Processing acknowledgment")
                
                elif data['type'] == 'fast_response':
                    elapsed = time.time() - start_time
                    msg_data = data['data']
                    
                    print(f"   ⏱️  Response time: {elapsed:.2f}s")
                    print(f"   💬 Content: {msg_data.get('content', '')[:100]}...")
                    print(f"   📊 Confidence: {msg_data.get('confidence', 0)}")
                    print(f"   📝 Reason: {msg_data.get('confidenceReason', '...')}")
                    print(f"   ❓ Questions: {msg_data.get('contextNeeds', [])}")
                    print(f"   ⚡ Actions: {msg_data.get('suggestedActions', [])}")
                
                elif data['type'] == 'analysis_status':
                    status = data['data'].get('status', '')
                    print(f"   🔄 Status: {status}")
                
                elif data['type'] == 'analysis_update':
                    print(f"   ✅ Full analysis received!")
                    analysis = data['data']
                    print(f"   → M1 DNA: {analysis.get('m1_dna', {}).get('summary', '')[:50]}...")
                    print(f"   → M2 Purchase Temp: {analysis.get('m2_indicators', {}).get('purchaseTemperature', 0)}")
                    break  # Analysis complete
                
                elif data['type'] == 'analysis_error':
                    print(f"   ❌ Analysis error: {data['data'].get('error', '')}")
            
            except asyncio.TimeoutError:
                print("   ⏸️  Waiting...")
                continue
        
        print(f"\n{'='*60}")
        print(f"Total responses: {response_count}")
        print(f"Elapsed time: {time.time() - start_time:.1f}s")

if __name__ == "__main__":
    asyncio.run(test_frontend_format())
