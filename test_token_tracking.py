#!/usr/bin/env python3
"""
Simple test to verify token tracking implementation
"""

def test_imports():
    """Test that all new modules can be imported."""
    try:
        from telemetry import (
            initialize_telemetry,
            track_openai_tokens,
            add_token_span_attributes,
            record_token_metrics,
            extract_token_usage,
            calculate_token_cost,
            instrument_semantic_kernel
        )
        print("✅ All telemetry imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_token_pricing():
    """Test token cost calculation."""
    try:
        from telemetry.token_tracking import calculate_token_cost
        
        # Test with known model
        cost = calculate_token_cost("gpt-4o", 1000, 500)
        expected = (1000/1000 * 0.005) + (500/1000 * 0.015)  # $0.005 + $0.0075 = $0.0125
        
        if abs(cost - expected) < 0.0001:
            print(f"✅ Token cost calculation correct: ${cost:.4f}")
            return True
        else:
            print(f"❌ Token cost calculation wrong: got ${cost:.4f}, expected ${expected:.4f}")
            return False
    except Exception as e:
        print(f"❌ Token cost calculation error: {e}")
        return False

def test_usage_extraction():
    """Test token usage extraction with mock response."""
    try:
        from telemetry.token_tracking import extract_token_usage
        
        # Mock OpenAI response structure
        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 100
                self.completion_tokens = 50
                self.total_tokens = 150
        
        class MockResponse:
            def __init__(self):
                self.usage = MockUsage()
        
        response = MockResponse()
        usage = extract_token_usage(response)
        
        expected = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
        
        if usage == expected:
            print("✅ Token usage extraction works correctly")
            return True
        else:
            print(f"❌ Token usage extraction failed: got {usage}, expected {expected}")
            return False
    except Exception as e:
        print(f"❌ Token usage extraction error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Token Tracking Implementation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_token_pricing, 
        test_usage_extraction
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Token tracking implementation is ready.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
