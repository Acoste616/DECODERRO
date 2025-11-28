"""
Quick test script to diagnose Gemini API issue
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Import AI Core
import sys
sys.path.insert(0, 'backend')

from ai_core import ai_core

async def test_fast_path():
    print("="*60)
    print("🔬 TESTING FAST PATH WITH GEMINI")
    print("="*60)
    
    # Simple test message
    history = [
        {"role": "user", "content": "Dzień dobry, interesuję się Teslą Model 3"}
    ]
    
    rag_context = "Tesla Model 3 to elektryczny samochód sedan premium."
    
    print(f"\n📝 Test Input:")
    print(f"- History: {len(history)} messages")
    print(f"- RAG Context length: {len(rag_context)} chars")
    print(f"- Stage: DISCOVERY")
    print(f"- Language: PL")
    
    print(f"\n🚀 Calling fast_path_secure...")
    
    try:
        response = await ai_core.fast_path_secure(
            history=history,
            rag_context=rag_context,
            stage="DISCOVERY",
            language="PL"
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"- Response length: {len(response.response)} chars")
        print(f"- Confidence: {response.confidence}")
        print(f"- Confidence reason: {response.confidence_reason[:100]}...")
        print(f"- Tactical steps: {len(response.tactical_next_steps)} items")
        print(f"- Knowledge gaps: {len(response.knowledge_gaps)} items")
        
        print(f"\n📄 Full Response:")
        print(response.response)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fast_path())
