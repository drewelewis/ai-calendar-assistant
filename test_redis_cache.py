#!/usr/bin/env python3
"""
Redis Cache Test Script for AI Calendar Assistant

This script tests the Redis caching implementation for Microsoft Graph operations.
Run this script to validate that caching is working correctly.
"""

import asyncio
import time
import os
import sys
from typing import Dict, Any

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from operations.graph_operations import GraphOperations
except ImportError as e:
    print(f"❌ Failed to import GraphOperations: {e}")
    print("Make sure you're running this from the correct directory and dependencies are installed.")
    sys.exit(1)

class CachePerformanceTester:
    """Test Redis cache performance for Graph operations."""
    
    def __init__(self):
        self.graph_ops = None
        self.test_results = {}
    
    async def setup(self):
        """Initialize the Graph operations client."""
        try:
            self.graph_ops = GraphOperations()
            print("✅ GraphOperations client initialized")
            
            # Test Redis connection
            redis_client = await self.graph_ops._get_redis_client()
            if redis_client:
                await redis_client.ping()
                print("✅ Redis connection successful")
            else:
                print("⚠️  Redis not available - testing without cache")
                
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise

    async def test_method_performance(self, method_name: str, method_func, *args, **kwargs) -> Dict[str, Any]:
        """Test cache performance for a specific method."""
        print(f"\n🔍 Testing {method_name}...")
        
        # First call (cache miss)
        print("   📤 Cache MISS test...")
        start_time = time.time()
        try:
            result1 = await method_func(*args, **kwargs)
            miss_time = time.time() - start_time
            print(f"   ⏱️  Miss time: {miss_time:.3f}s")
        except Exception as e:
            print(f"   ❌ Miss test failed: {e}")
            return {"error": str(e)}
        
        # Small delay to ensure different timestamps
        await asyncio.sleep(0.1)
        
        # Second call (cache hit)
        print("   📥 Cache HIT test...")
        start_time = time.time()
        try:
            result2 = await method_func(*args, **kwargs)
            hit_time = time.time() - start_time
            print(f"   ⏱️  Hit time: {hit_time:.3f}s")
        except Exception as e:
            print(f"   ❌ Hit test failed: {e}")
            return {"error": str(e)}
        
        # Calculate performance improvement
        if hit_time > 0:
            improvement = miss_time / hit_time
            print(f"   🚀 Performance improvement: {improvement:.1f}x")
        else:
            improvement = float('inf')
            print(f"   🚀 Performance improvement: ∞ (instant)")
        
        # Verify results are consistent
        result_consistent = str(result1) == str(result2)
        print(f"   ✅ Results consistent: {result_consistent}")
        
        return {
            "miss_time": miss_time,
            "hit_time": hit_time,
            "improvement": improvement,
            "consistent": result_consistent,
            "result_size": len(str(result1)) if result1 else 0
        }

    async def run_comprehensive_tests(self):
        """Run comprehensive cache performance tests."""
        print("🧪 Starting Redis Cache Performance Tests")
        print("=" * 60)
        
        # Test 1: User lookup by ID (if we have a valid user ID)
        print("\n📋 Test 1: User Information Caching")
        try:
            # First get a list of users to test with
            users = await self.graph_ops.get_all_users(5, exclude_inactive_mailboxes=True)
            if users and len(users) > 0:
                test_user_id = users[0].id
                self.test_results["get_user_by_user_id"] = await self.test_method_performance(
                    "get_user_by_user_id",
                    self.graph_ops.get_user_by_user_id,
                    test_user_id
                )
            else:
                print("   ⚠️  No users found for testing user lookup")
        except Exception as e:
            print(f"   ❌ User lookup test failed: {e}")
        
        # Test 2: All users
        print("\n📋 Test 2: All Users Caching")
        self.test_results["get_all_users"] = await self.test_method_performance(
            "get_all_users",
            self.graph_ops.get_all_users,
            10,  # max_results
            True  # exclude_inactive_mailboxes
        )
        
        # Test 3: Departments
        print("\n📋 Test 3: Departments Caching")
        self.test_results["get_all_departments"] = await self.test_method_performance(
            "get_all_departments",
            self.graph_ops.get_all_departments,
            50  # max_results
        )
        
        # Test 4: Conference rooms
        print("\n📋 Test 4: Conference Rooms Caching")
        self.test_results["get_all_conference_rooms"] = await self.test_method_performance(
            "get_all_conference_rooms",
            self.graph_ops.get_all_conference_rooms,
            20  # max_results
        )
        
        # Test 5: Search users
        print("\n📋 Test 5: User Search Caching")
        self.test_results["search_users"] = await self.test_method_performance(
            "search_users",
            self.graph_ops.search_users,
            "department eq 'Engineering'",  # filter
            10,  # max_results
            True  # exclude_inactive_mailboxes
        )

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 REDIS CACHE PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if "error" not in result)
        
        print(f"Tests Run: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        
        if successful_tests > 0:
            print("\n🏆 Performance Results:")
            print("-" * 60)
            print(f"{'Method':<25} {'Miss Time':<12} {'Hit Time':<12} {'Improvement':<12}")
            print("-" * 60)
            
            total_improvement = 0
            for method, result in self.test_results.items():
                if "error" not in result:
                    print(f"{method:<25} {result['miss_time']:.3f}s{'':<6} {result['hit_time']:.3f}s{'':<6} {result['improvement']:.1f}x")
                    if result['improvement'] != float('inf'):
                        total_improvement += result['improvement']
                else:
                    print(f"{method:<25} ERROR: {result['error']}")
            
            if successful_tests > 0:
                avg_improvement = total_improvement / successful_tests
                print("-" * 60)
                print(f"Average Performance Improvement: {avg_improvement:.1f}x")
        
        print("\n💡 Cache Configuration:")
        print(f"   Redis Enabled: {self.graph_ops.cache_enabled if self.graph_ops else 'Unknown'}")
        print(f"   Redis URL: {self.graph_ops.redis_url if self.graph_ops else 'Unknown'}")
        
        if self.graph_ops and self.graph_ops.cache_enabled:
            print("   TTL Configuration:")
            for cache_type, ttl in self.graph_ops.cache_ttl_config.items():
                print(f"     {cache_type}: {ttl}s ({ttl//60}m)")

    async def cleanup(self):
        """Clean up resources."""
        if self.graph_ops:
            await self.graph_ops.close_cache()
            print("\n🔒 Redis connection closed")

async def main():
    """Main test function."""
    tester = CachePerformanceTester()
    
    try:
        await tester.setup()
        await tester.run_comprehensive_tests()
        tester.print_summary()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    print("🚀 AI Calendar Assistant - Redis Cache Performance Tester")
    print("This script tests the caching performance of Graph operations.\n")
    
    # Check environment
    redis_enabled = os.environ.get('REDIS_CACHE_ENABLED', 'true').lower() in ('true', '1', 'yes')
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    print(f"Environment Configuration:")
    print(f"  Redis Enabled: {redis_enabled}")
    print(f"  Redis URL: {redis_url}")
    print(f"  Graph Client: {'Configured' if all(os.environ.get(var) for var in ['ENTRA_GRAPH_APPLICATION_TENANT_ID', 'ENTRA_GRAPH_APPLICATION_CLIENT_ID', 'ENTRA_GRAPH_APPLICATION_CLIENT_SECRET']) else 'Not Configured'}")
    
    if not redis_enabled:
        print("\n⚠️  Redis caching is disabled. Enable it by setting REDIS_CACHE_ENABLED=true")
    
    print("\nStarting tests...\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
