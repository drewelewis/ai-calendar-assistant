#!/usr/bin/env python3
"""
Debug script to show cache key generation for get_all_users calls
"""
import hashlib
from datetime import datetime

def generate_cache_key(method_name: str, *args, **kwargs) -> str:
    """Replicate the updated cache key generation logic with normalization"""
    key_parts = [method_name]
    
    # Special handling for get_all_users to normalize max_results for consistent caching
    if method_name == "get_all_users":
        # Always use 100 as max_results in cache key for consistency
        normalized_args = list(args)
        if len(normalized_args) > 0:
            normalized_args[0] = 100  # Force max_results to 100 in cache key
        
        # Add normalized positional arguments
        for arg in normalized_args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, datetime):
                key_parts.append(arg.isoformat())
            else:
                key_parts.append(str(hash(str(arg))))
    else:
        # Add positional arguments normally for other methods
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, datetime):
                key_parts.append(arg.isoformat())
            else:
                key_parts.append(str(hash(str(arg))))
    
    # Add keyword arguments in sorted order for consistency
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
        elif isinstance(v, datetime):
            key_parts.append(f"{k}:{v.isoformat()}")
        else:
            key_parts.append(f"{k}:{hash(str(v))}")
    
    # Create hash to keep key length manageable
    key_string = "|".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"graph:{method_name}:{key_hash}"

print("🔍 Cache Key Analysis for get_all_users calls")
print("=" * 60)

# Different ways get_all_users might be called
test_calls = [
    ("Default plugin call", "get_all_users", [100, True], {}),
    ("Plugin with defaults", "get_all_users", [100], {"exclude_inactive_mailboxes": True}),
    ("Test call 1", "get_all_users", [5, False], {}),
    ("Test call 2", "get_all_users", [5, True], {}),
    ("Test call 3", "get_all_users", [5], {"exclude_inactive_mailboxes": False}),
    ("Test call 4", "get_all_users", [5], {"exclude_inactive_mailboxes": True}),
    ("Debug call", "get_all_users", [10, True], {}),
    ("No params", "get_all_users", [], {}),
]

for description, method, args, kwargs in test_calls:
    cache_key = generate_cache_key(method, *args, **kwargs)
    
    # Show the key components for debugging - use normalized args for get_all_users
    key_parts = [method]
    
    if method == "get_all_users":
        # Show normalized args
        normalized_args = list(args)
        if len(normalized_args) > 0:
            normalized_args[0] = 100  # Force max_results to 100 in cache key
        for arg in normalized_args:
            key_parts.append(str(arg))
    else:
        for arg in args:
            key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    
    key_string = "|".join(key_parts)
    
    print(f"\n📋 {description}")
    print(f"   Call: {method}({', '.join(map(str, args))}{', ' if args and kwargs else ''}{', '.join(f'{k}={v}' for k, v in kwargs.items())})")
    print(f"   Normalized Key String: {key_string}")
    print(f"   Cache Key: {cache_key}")

print("\n" + "=" * 60)
print("🔍 ANALYSIS:")
print("✅ Calls with same exclude_inactive_mailboxes value should have SAME cache key")
print("   - get_all_users(100, True) = get_all_users(5, True) = get_all_users(10, True)")
print("   - get_all_users(5, False) should be different from True calls")
print("   - Keyword vs positional args may still create different keys")

print("\n" + "=" * 60)
print("🎉 SOLUTION IMPLEMENTED: Cache key normalization for get_all_users!")
print("   Different max_results values now generate the SAME cache key.")
print("   This means consistent caching regardless of the parameter passed.")
print("   The actual API call still uses 100 for consistent LLM behavior.")
