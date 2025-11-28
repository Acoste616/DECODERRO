"""
Test Enhanced Fast Path with real user question
"""

import asyncio
import websockets
import json
import time

async def test_enhanced_prompt():
    session_id = f"enhance-test-{int(time.time())}"
    url = f"ws://localhost:8000/ws/chat/{session_id}"
    
    print("🧪 Testing Enhanced Fast Path Prompt")
    print("="*60)
    
    async with websockets.connect(url) as ws:
        # Real user question from screenshot
        message = {
            "content": "klient pyta o dopłaty, martwi się zasięgiem w zimie, pyta o koszty serwisu"
        }
        
        print(f"\n📤 User Question:")
        print(f"   {message['content']}")
        print(f"\n⏱️  Waiting for response...")
        
        await ws.send(json.dumps(message))
        
        start = time.time()
        
        while time.time() - start < 10:
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(response)
                
                if data['type'] == 'fast_response':
                    elapsed = time.time() - start
                    msg = data['data']
                    
                    print(f"\n✅ FAST PATH RESPONSE ({elapsed:.2f}s)")
                    print("="*60)
                    print(f"\n💬 Content:")
                    print(f"   {msg.get('content', '')}")
                    print(f"\n📊 Confidence: {msg.get('confidence', 0):.2f}")
                    print(f"📝 Reason: {msg.get('confidenceReason', '')}")
                    print(f"\n❓ Questions for Salesperson:")
                    for q in msg.get('contextNeeds', []):
                        print(f"   - {q}")
                    print(f"\n⚡ Actions for Client:")
                    for a in msg.get('suggestedActions', []):
                        print(f"   - {a}")
                    
                    # Evaluate quality
                    content = msg.get('content', '').lower()
                    print(f"\n🔍 Quality Check:")
                    print(f"   Mentions 'dopłaty/dotacja': {'✅' if 'dopł' in content or 'dotac' in content else '❌'}")
                    print(f"   Mentions 'zima/zasięg': {'✅' if 'zim' in content or 'zasięg' in content else '❌'}")
                    print(f"   Mentions 'serwis/koszty': {'✅' if 'serwis' in content or 'koszt' in content else '❌'}")
                    print(f"   Uses RAG data (numbers): {'✅' if any(c.isdigit() for c in content) else '❌'}")
                    
                    break
            
            except asyncio.TimeoutError:
                continue
        
        print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_enhanced_prompt())
