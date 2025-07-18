#!/usr/bin/env python3
"""
Enhanced API Test Script
Tests the new LLM analytics and cost calculation features.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class EnhancedAPITester:
    """Test the enhanced API with LLM analytics."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        
    async def test_llm_models_endpoint(self):
        """Test the LLM models and pricing endpoint."""
        print("\n🤖 Testing LLM Models Endpoint")
        print("=" * 50)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/llm_models") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Successfully retrieved model information")
                        
                        # Display models in a formatted way
                        models = data["data"]["🤖 azure_openai_models"]
                        print(f"\n📋 Available Azure OpenAI Models ({len(models)} total):")
                        
                        for model in models:
                            print(f"\n🔸 {model['model_name']}")
                            print(f"   💰 Input:  {model['input_cost_per_1k']}/1K tokens")
                            print(f"   💰 Output: {model['output_cost_per_1k']}/1K tokens")
                            print(f"   📊 Ratio:  {model['cost_ratio']}")
                            print(f"   🎯 Use:    {model['use_case']}")
                        
                        # Display pricing info
                        pricing_info = data["data"]["💡 pricing_information"]
                        print(f"\n📝 Pricing Notes:")
                        for note in pricing_info["notes"]:
                            print(f"   • {note}")
                            
                        print(f"\n🔧 Current Deployment: {pricing_info['current_deployment']}")
                        
                    else:
                        print(f"❌ Failed with status: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error testing models endpoint: {e}")
    
    async def test_cost_calculation(self):
        """Test the cost calculation endpoint."""
        print("\n💰 Testing Cost Calculation Endpoint")
        print("=" * 50)
        
        # Test different scenarios
        test_scenarios = [
            {
                "name": "Small Chat Message",
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "model_name": "gpt-4o-mini"
            },
            {
                "name": "Large Document Analysis",
                "prompt_tokens": 2000,
                "completion_tokens": 500,
                "model_name": "gpt-4o"
            },
            {
                "name": "Complex Reasoning Task",
                "prompt_tokens": 1500,
                "completion_tokens": 800,
                "model_name": "gpt-4-turbo"
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for scenario in test_scenarios:
                print(f"\n🧪 Testing: {scenario['name']}")
                
                try:
                    payload = {
                        "prompt_tokens": scenario["prompt_tokens"],
                        "completion_tokens": scenario["completion_tokens"],
                        "model_name": scenario["model_name"]
                    }
                    
                    async with session.post(
                        f"{self.base_url}/calculate_cost",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            calc = data["calculation"]
                            
                            print(f"   📊 Model: {calc['🤖 model_used']}")
                            print(f"   🔢 Tokens: {calc['🔢 input_tokens']} + {calc['🔢 output_tokens']} = {calc['🔢 total_tokens']}")
                            print(f"   💰 Cost: {calc['💰 cost_breakdown']['total_cost']}")
                            print(f"   📈 Daily (100 calls): {calc['📈 projections']['daily_estimate_100_calls']}")
                            print(f"   📈 Monthly (1K calls): {calc['📈 projections']['monthly_estimate_1k_calls']}")
                            print(f"   ⚡ Efficiency: {calc['⚡ efficiency']}")
                            
                        else:
                            print(f"   ❌ Failed with status: {response.status}")
                            
                except Exception as e:
                    print(f"   ❌ Error: {e}")
    
    async def test_enhanced_chat(self):
        """Test the enhanced chat endpoints with analytics."""
        print("\n💬 Testing Enhanced Chat Endpoints")
        print("=" * 50)
        
        test_message = {
            "session_id": f"test-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "message": "Hello! Can you help me schedule a meeting for tomorrow?"
        }
        
        async with aiohttp.ClientSession() as session:
            # Test single agent chat
            print("\n🤖 Testing Single Agent Chat:")
            try:
                async with session.post(
                    f"{self.base_url}/agent_chat",
                    json=test_message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Single agent chat successful")
                        
                        # Display analytics if present
                        if "📊 llm_analytics" in data:
                            analytics = data["📊 llm_analytics"]
                            print(f"   🤖 Model: {analytics['🤖 model_details']['detected_model']}")
                            print(f"   🔢 Tokens: {analytics['🔢 token_usage']['total_tokens']}")
                            print(f"   💰 Cost: {analytics['💰 cost_analysis']['total_cost']}")
                            print(f"   📈 Projection: {analytics['📈 cost_projections']['daily_100_calls']}/day")
                        
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed with status: {response.status} - {error_text}")
                        
            except Exception as e:
                print(f"❌ Error testing single agent: {e}")
            
            # Test multi-agent chat
            print("\n🤖🤖 Testing Multi-Agent Chat:")
            try:
                async with session.post(
                    f"{self.base_url}/multi_agent_chat",
                    json=test_message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Multi-agent chat successful")
                        
                        # Display analytics if present
                        if "📊 llm_analytics" in data:
                            analytics = data["📊 llm_analytics"]
                            print(f"   🤖 Model: {analytics['🤖 model_details']['detected_model']}")
                            print(f"   🔢 Tokens: {analytics['🔢 token_usage']['total_tokens']} (estimated)")
                            print(f"   💰 Cost: {analytics['💰 cost_analysis']['total_cost']}")
                            print(f"   📈 Projection: {analytics['📈 cost_projections']['daily_100_calls']}/day")
                        
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed with status: {response.status} - {error_text}")
                        
            except Exception as e:
                print(f"❌ Error testing multi-agent: {e}")
    
    async def run_all_tests(self):
        """Run all enhanced API tests."""
        print("🚀 Enhanced API Test Suite")
        print("=" * 70)
        print(f"Testing API at: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        await self.test_llm_models_endpoint()
        await self.test_cost_calculation()
        await self.test_enhanced_chat()
        
        print("\n✅ All tests completed!")
        print("=" * 70)

async def main():
    """Main test runner."""
    tester = EnhancedAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
