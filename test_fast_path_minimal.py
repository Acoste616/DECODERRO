import asyncio
from backend.ai_core import AICore

async def test_fast_path():
    ai_core = AICore()
    
    history = [
        {"role": "user", "content": "Cześć, pytam o Model 3"}
    ]
    
    context = "[TEST] Price: 229,990 PLN"
    stage = "DISCOVERY"
    
    print("[TEST] Calling ai_core.fast_path()...")
    try:
        result = await ai_core.fast_path(
            history=history,
            context=context,
            stage=stage,
            language="PL",
            stream=False
        )
        print(f"[SUCCESS] Response: {result.response[:100]}...")
        print(f"[SUCCESS] Confidence: {result.confidence}")
        return True
    except Exception as e:
        print(f"[ERROR] Fast Path failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fast_path())
    exit(0 if success else 1)
