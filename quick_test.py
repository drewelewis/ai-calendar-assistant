#!/usr/bin/env python3
"""
Quick test to check if the multi-agent fix works
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Real M365 user ID — allows Graph API calls to work in smoke tests
SMOKE_SESSION_ID = "9480ffca-a008-40f2-8e81-d29d633c04ea"
# Suppress Teams notifications so smoke test messages don't appear in the user's Teams client
os.environ["DISABLE_TEAMS_NOTIFICATIONS"] = "true"

async def quick_test():
    try:
        from ai.multi_agent import MultiAgentOrchestrator
        print("✅ MultiAgentOrchestrator imported successfully")
        
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(session_id=SMOKE_SESSION_ID)
        print("✅ MultiAgentOrchestrator created successfully")
        
        # Test the process_message method
        result = await orchestrator.process_message("Can you help me schedule a meeting?")
        print(f"✅ Message processed successfully!")
        print(f"Response: {result[:100]}..." if len(result) > 100 else f"Response: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(quick_test())
