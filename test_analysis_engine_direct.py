import asyncio
import os
from dotenv import load_dotenv
from backend.analysis_engine import analysis_engine

# Force reload env to be sure
load_dotenv(override=True)

async def test_engine():
    print("Testing AnalysisEngine directly...")
    print(f"Model: {analysis_engine.model}")
    print(f"Base URL: {analysis_engine.base_url}")
    print(f"API Key present: {bool(analysis_engine.api_key)}")
    
    # Mock chat history
    history = [
        {"role": "user", "content": "Cześć, szukam samochodu."},
        {"role": "assistant", "content": "Dzień dobry! Jakiego typu auta szukasz?"},
        {"role": "user", "content": "Chyba SUV, coś bezpiecznego dla rodziny."}
    ]
    
    print("\nRunning deep analysis...")
    result = await analysis_engine.run_deep_analysis("test_session", history)
    
    print("\nResult:")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_engine())
