"""
ULTRA v3.0 - Test RAG Fallback Response
Verifies that RAG fallback returns natural language, not raw database text.
"""

from ai_core import create_rag_fallback_response

def test_rag_fallback_natural_language():
    """Test that RAG fallback returns natural Polish sales response."""
    
    # Sample RAG context with raw database markers
    sample_rag = "[Info]: [Identyfikacja] Tesla Model 3 to sedan premium..."
    
    # Get fallback response
    response = create_rag_fallback_response(sample_rag, language="PL")
    
    # ASSERT 1: Response should NOT contain raw database markers
    assert "[Info]:" not in response.response, "❌ Response contains raw database marker '[Info]:'"
    assert "[Identyfikacja]" not in response.response, "❌ Response contains raw database marker '[Identyfikacja]'"
    assert "Na podstawie naszej bazy danych:" not in response.response, "❌ Response exposes database internals"
    
    # ASSERT 2: Response should be natural Polish text
    assert len(response.response) > 20, "❌ Response is too short"
    assert "Tesla" in response.response or "pytanie" in response.response, "❌ Response doesn't seem contextual"
    
    # ASSERT 3: Tactical next steps should have at least 2 items
    assert len(response.tactical_next_steps) >= 2, f"❌ Only {len(response.tactical_next_steps)} tactical steps (need 2+)"
    
    # ASSERT 4: Knowledge gaps should have at least 2 items
    assert len(response.knowledge_gaps) >= 2, f"❌ Only {len(response.knowledge_gaps)} knowledge gaps (need 2+)"
    
    # ASSERT 5: Confidence should be reasonable
    assert 0.5 <= response.confidence <= 1.0, f"❌ Confidence {response.confidence} is out of range"
    
    print("✅ RAG Fallback Test PASSED!")
    print(f"   Response: {response.response[:80]}...")
    print(f"   Tactical Steps: {len(response.tactical_next_steps)}")
    print(f"   Knowledge Gaps: {len(response.knowledge_gaps)}")
    print(f"   Confidence: {response.confidence}")
    

def test_rag_fallback_english():
    """Test English fallback as well."""
    
    sample_rag = "[Info]: Tesla Model 3 is a premium sedan..."
    response = create_rag_fallback_response(sample_rag, language="EN")
    
    assert "[Info]:" not in response.response
    assert "Based on our database:" not in response.response
    assert len(response.tactical_next_steps) >= 2
    assert len(response.knowledge_gaps) >= 2
    
    print("✅ English RAG Fallback Test PASSED!")


if __name__ == "__main__":
    print("\n🔬 Testing RAG Fallback Response...")
    print("=" * 60)
    
    try:
        test_rag_fallback_natural_language()
        test_rag_fallback_english()
        print("=" * 60)
        print("🎉 ALL TESTS PASSED! RAG fallback is now natural language.")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("=" * 60)
        exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
