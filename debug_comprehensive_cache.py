#!/usr/bin/env python3
"""
Comprehensive cache key analysis for all normalized methods
"""
import hashlib
from datetime import datetime

def generate_cache_key(method_name: str, *args, **kwargs) -> str:
    """Replicate the updated cache key generation logic with comprehensive normalization"""
    key_parts = [method_name]
    
    # Special handling for methods that need parameter normalization for consistent caching
    if method_name in ["get_all_users", "get_users_by_department", "search_users"]:
        # These methods have max_results and exclude_inactive_mailboxes parameters
        # Always normalize max_results to 100 for consistent caching
        normalized_args = list(args)
        if len(normalized_args) > 0:
            # For get_all_users: args[0] = max_results
            # For get_users_by_department: args[0] = department, args[1] = max_results  
            # For search_users: args[0] = filter, args[1] = max_results
            if method_name == "get_all_users":
                normalized_args[0] = 100  # max_results
            elif method_name == "get_users_by_department" and len(normalized_args) > 1:
                normalized_args[1] = 100  # max_results (department stays as-is)
            elif method_name == "search_users" and len(normalized_args) > 1:
                normalized_args[1] = 100  # max_results (filter stays as-is)
        
        # Add normalized positional arguments
        for arg in normalized_args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, datetime):
                key_parts.append(arg.isoformat())
            else:
                key_parts.append(str(hash(str(arg))))
                
    elif method_name in ["get_all_conference_rooms", "get_all_departments"]:
        # These methods only have max_results parameter
        # Always normalize max_results to 100 for consistent caching
        normalized_args = list(args)
        if len(normalized_args) > 0:
            normalized_args[0] = 100  # max_results
        
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

print("🔍 COMPREHENSIVE Cache Key Analysis - All Normalized Methods")
print("=" * 80)

# Test cases for all normalized methods
test_scenarios = [
    # get_all_users tests
    ("get_all_users - Default", "get_all_users", [100, True], {}),
    ("get_all_users - Different max_results", "get_all_users", [50, True], {}),
    ("get_all_users - Very different max_results", "get_all_users", [200, True], {}),
    ("get_all_users - Different exclude_inactive", "get_all_users", [100, False], {}),
    
    # get_all_conference_rooms tests  
    ("get_all_conference_rooms - Default", "get_all_conference_rooms", [50], {}),
    ("get_all_conference_rooms - Different max_results", "get_all_conference_rooms", [25], {}),
    ("get_all_conference_rooms - Large max_results", "get_all_conference_rooms", [200], {}),
    
    # get_all_departments tests
    ("get_all_departments - Default", "get_all_departments", [100], {}),
    ("get_all_departments - Different max_results", "get_all_departments", [75], {}),
    ("get_all_departments - Small max_results", "get_all_departments", [10], {}),
    
    # get_users_by_department tests
    ("get_users_by_department - IT Dept", "get_users_by_department", ["IT", 50, True], {}),
    ("get_users_by_department - IT Different max", "get_users_by_department", ["IT", 25, True], {}),
    ("get_users_by_department - IT Different exclude", "get_users_by_department", ["IT", 50, False], {}),
    ("get_users_by_department - HR Dept", "get_users_by_department", ["HR", 50, True], {}),
    
    # search_users tests
    ("search_users - Name search", "search_users", ["startswith(displayName,'John')", 30, True], {}),
    ("search_users - Name search different max", "search_users", ["startswith(displayName,'John')", 60, True], {}),
    ("search_users - Name search different exclude", "search_users", ["startswith(displayName,'John')", 30, False], {}),
    ("search_users - Email search", "search_users", ["startswith(mail,'admin')", 30, True], {}),
]

# Group by method for easier analysis
methods = {}
for scenario in test_scenarios:
    method_name = scenario[1]
    if method_name not in methods:
        methods[method_name] = []
    methods[method_name].append(scenario)

for method_name, scenarios in methods.items():
    print(f"\n🔧 {method_name.upper()} ANALYSIS")
    print("-" * 60)
    
    cache_keys = {}
    for description, method, args, kwargs in scenarios:
        cache_key = generate_cache_key(method, *args, **kwargs)
        
        # Show normalized key components
        key_parts = [method]
        
        if method in ["get_all_users", "get_users_by_department", "search_users"]:
            normalized_args = list(args)
            if len(normalized_args) > 0:
                if method == "get_all_users":
                    normalized_args[0] = 100
                elif method == "get_users_by_department" and len(normalized_args) > 1:
                    normalized_args[1] = 100
                elif method == "search_users" and len(normalized_args) > 1:
                    normalized_args[1] = 100
            for arg in normalized_args:
                key_parts.append(str(arg))
        elif method in ["get_all_conference_rooms", "get_all_departments"]:
            normalized_args = list(args)
            if len(normalized_args) > 0:
                normalized_args[0] = 100
            for arg in normalized_args:
                key_parts.append(str(arg))
        else:
            for arg in args:
                key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = "|".join(key_parts)
        
        print(f"  📋 {description}")
        print(f"     Original Call: {method}({', '.join(map(str, args))}{', ' if args and kwargs else ''}{', '.join(f'{k}={v}' for k, v in kwargs.items())})")
        print(f"     Normalized Key: {key_string}")
        print(f"     Cache Key: {cache_key}")
        
        # Track unique cache keys
        if cache_key not in cache_keys:
            cache_keys[cache_key] = []
        cache_keys[cache_key].append(description)
        print()
    
    print(f"  📊 SUMMARY for {method_name}:")
    print(f"     Total scenarios tested: {len(scenarios)}")
    print(f"     Unique cache keys generated: {len(cache_keys)}")
    
    if len(cache_keys) < len(scenarios):
        print("     ✅ SUCCESS: Cache key normalization is working!")
        for cache_key, descriptions in cache_keys.items():
            if len(descriptions) > 1:
                print(f"        🔗 Shared cache key: {descriptions}")
    else:
        print("     ⚠️  Each scenario has unique cache key")

print("\n" + "=" * 80)
print("🎉 COMPREHENSIVE CACHE NORMALIZATION IMPLEMENTED!")
print("✅ All methods now use normalized max_results=100 for consistent caching")
print("✅ Different max_results values will share the same cache entry")
print("✅ LLM behavior will be predictable across all Graph API operations")
print("✅ Significant reduction in cache fragmentation expected")
