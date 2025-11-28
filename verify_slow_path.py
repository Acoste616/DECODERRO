import asyncio
import os
from backend.ai import generate_deep_analysis

async def verify_slow_path():
    print("Initializing verification for backend.ai...")
    
    history = [
        {"role": "user", "content": "Dzień dobry, szukam samochodu dla rodziny, ale boję się elektryków."},
        {"role": "ai", "content": "Rozumiem Pana obawy. Wiele osób ma podobne wątpliwości na początku. Co konkretnie Pana martwi? Zasięg, ładowanie czy może coś innego?"},
        {"role": "user", "content": "Głównie zasięg w zimie i to, że nie mam gdzie ładować w bloku. Jeżdżę dużo w trasy, około 500km tygodniowo."}
    ]
    
    print("Starting Slow Path Analysis (backend.ai)...")
    try:
        result = await generate_deep_analysis(history)
        
        if result:
            print("\n✅ Slow Path Analysis Successful!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("\n❌ Slow Path Analysis Failed (returned empty)")
            
    except Exception as e:
        print(f"\n❌ Error during Slow Path: {e}")

if __name__ == "__main__":
    import json
    asyncio.run(verify_slow_path())
