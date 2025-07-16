#!/usr/bin/env python3
"""
Test script to verify telemetry error handling robustness.
This simulates the CompletionUsage object scenario that was causing the production error.
"""

class MockCompletionUsage:
    """Mock CompletionUsage object to simulate the production error scenario."""
    def __init__(self, prompt_tokens=100, completion_tokens=50, total_tokens=150):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
    
    # Intentionally missing .get() method to replicate the error

def test_extract_token_usage():
    """Test the _extract_token_usage function with different input types."""
    from telemetry.semantic_kernel_instrumentation import _extract_token_usage
    
    print("Testing _extract_token_usage function...")
    
    # Test with dictionary (should work)
    dict_usage = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150
    }
    result = _extract_token_usage(dict_usage)
    print(f"✅ Dictionary usage: {result}")
    assert result["prompt_tokens"] == 100
    assert result["completion_tokens"] == 50
    assert result["total_tokens"] == 150
    
    # Test with CompletionUsage object (should work with our fix)
    obj_usage = MockCompletionUsage(200, 75, 275)
    result = _extract_token_usage(obj_usage)
    print(f"✅ Object usage: {result}")
    assert result["prompt_tokens"] == 200
    assert result["completion_tokens"] == 75
    assert result["total_tokens"] == 275
    
    # Test with None (should handle gracefully)
    result = _extract_token_usage(None)
    print(f"✅ None usage: {result}")
    assert result["prompt_tokens"] == 0
    assert result["completion_tokens"] == 0
    assert result["total_tokens"] == 0
    
    # Test with empty object (should handle gracefully)
    class EmptyObject:
        pass
    
    empty_obj = EmptyObject()
    result = _extract_token_usage(empty_obj)
    print(f"✅ Empty object usage: {result}")
    assert result["prompt_tokens"] == 0
    assert result["completion_tokens"] == 0
    assert result["total_tokens"] == 0
    
    print("🎉 All tests passed! Telemetry is now robust against token usage extraction errors.")

if __name__ == "__main__":
    test_extract_token_usage()
