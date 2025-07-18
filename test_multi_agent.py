#!/usr/bin/env python3
"""
Multi-Agent System Test Suite
Tests the multi-agent orchestrator functionality.
"""

import asyncio
import uuid
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.multi_agent import MultiAgentOrchestrator
from telemetry.console_output import console_info, console_error, console_success, console_warning

load_dotenv()

class MultiAgentTester:
    """Test suite for the multi-agent system."""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.orchestrator = None
        self.test_results = []
    
    async def setup(self):
        """Initialize the multi-agent system for testing."""
        try:
            console_info("🧪 Setting up multi-agent test environment...", "TEST")
            console_info(f"📋 Using test session ID: {self.session_id}", "TEST")
            self.orchestrator = MultiAgentOrchestrator(session_id=self.session_id)
            console_success("✅ Multi-agent system initialized for testing", "TEST")
            return True
        except Exception as e:
            console_error(f"❌ Setup failed: {e}", "TEST")
            return False
    
    async def test_system_status(self):
        """Test system status and agent availability."""
        console_info("🔍 Testing system status...", "TEST")
        
        try:
            status = await self.orchestrator.get_agent_status()
            
            # Validate status structure
            required_keys = ['session_id', 'total_agents', 'agents', 'cosmos_available', 'telemetry_enabled']
            for key in required_keys:
                if key not in status:
                    raise ValueError(f"Missing status key: {key}")
            
            # Check agent count
            if status['total_agents'] != 4:
                raise ValueError(f"Expected 4 agents, got {status['total_agents']}")
            
            # Check agent names
            expected_agents = ['ProxyAgent', 'CalendarAgent', 'DirectoryAgent', 'LocationAgent']
            for agent_name in expected_agents:
                if agent_name not in status['agents']:
                    raise ValueError(f"Missing agent: {agent_name}")
            
            console_success("✅ System status test passed", "TEST")
            self.test_results.append(("System Status", True, None))
            
        except Exception as e:
            console_error(f"❌ System status test failed: {e}", "TEST")
            self.test_results.append(("System Status", False, str(e)))
    
    async def test_agent_routing(self):
        """Test intelligent agent routing based on message content."""
        console_info("🎯 Testing agent routing...", "TEST")
        
        test_cases = [
            ("Hello, how can you help me?", "ProxyAgent"),
            ("Schedule a meeting tomorrow at 2 PM", "CalendarAgent"), 
            ("Find John Smith in our directory", "DirectoryAgent"),
            ("What coffee shops are nearby?", "LocationAgent"),
            ("What are my upcoming meetings?", "CalendarAgent"),
            ("Search for users in engineering", "DirectoryAgent"),
            ("Find restaurants near downtown", "LocationAgent")
        ]
        
        for message, expected_agent in test_cases:
            try:
                # Test routing logic (without full processing)
                selected_agent = self.orchestrator._select_agent_for_message(message)
                
                if selected_agent != expected_agent:
                    raise ValueError(f"Expected {expected_agent}, got {selected_agent}")
                
                console_success(f"✅ Routing test passed: '{message[:30]}...' → {selected_agent}", "TEST")
                
            except Exception as e:
                console_error(f"❌ Routing test failed for '{message[:30]}...': {e}", "TEST")
                self.test_results.append(("Agent Routing", False, str(e)))
                return
        
        self.test_results.append(("Agent Routing", True, None))
    
    async def test_conversation_flow(self):
        """Test basic conversation flow with the proxy agent."""
        console_info("💬 Testing conversation flow...", "TEST")
        
        try:
            # Test a simple greeting
            response = await self.orchestrator.process_message("Hello!")
            
            if not response or len(response) < 10:
                raise ValueError("Response too short or empty")
            
            if "error" in response.lower() or "failed" in response.lower():
                raise ValueError(f"Error in response: {response}")
            
            console_success(f"✅ Conversation test passed - Response: {response[:50]}...", "TEST")
            self.test_results.append(("Conversation Flow", True, None))
            
        except Exception as e:
            console_error(f"❌ Conversation test failed: {e}", "TEST")
            self.test_results.append(("Conversation Flow", False, str(e)))
    
    async def test_reset_functionality(self):
        """Test conversation reset functionality."""
        console_info("🔄 Testing reset functionality...", "TEST")
        
        try:
            # Send a message first
            await self.orchestrator.process_message("Remember this: test message")
            
            # Reset conversation
            await self.orchestrator.reset_conversation()
            
            console_success("✅ Reset test passed", "TEST")
            self.test_results.append(("Reset Functionality", True, None))
            
        except Exception as e:
            console_error(f"❌ Reset test failed: {e}", "TEST")
            self.test_results.append(("Reset Functionality", False, str(e)))
    
    async def test_error_handling(self):
        """Test error handling with invalid inputs."""
        console_info("⚠️ Testing error handling...", "TEST")
        
        try:
            # Test empty message
            response = await self.orchestrator.process_message("")
            if not response:
                raise ValueError("No response to empty message")
            
            # Test very long message
            long_message = "x" * 10000
            response = await self.orchestrator.process_message(long_message)
            if not response:
                raise ValueError("No response to long message")
            
            console_success("✅ Error handling test passed", "TEST")
            self.test_results.append(("Error Handling", True, None))
            
        except Exception as e:
            console_error(f"❌ Error handling test failed: {e}", "TEST")
            self.test_results.append(("Error Handling", False, str(e)))
    
    async def test_session_id_validation(self):
        """Test that session_id is required for initialization."""
        console_info("🔐 Testing session ID validation...", "TEST")
        
        try:
            # Test missing session_id should raise ValueError
            try:
                invalid_orchestrator = MultiAgentOrchestrator(session_id=None)
                raise ValueError("Expected ValueError for missing session_id")
            except ValueError as ve:
                if "Session ID is required" in str(ve):
                    console_success("✅ Session ID validation working correctly", "TEST")
                else:
                    raise ValueError(f"Unexpected error message: {ve}")
            
            # Test empty string session_id should also raise ValueError  
            try:
                invalid_orchestrator = MultiAgentOrchestrator(session_id="")
                raise ValueError("Expected ValueError for empty session_id")
            except ValueError as ve:
                if "Session ID is required" in str(ve):
                    console_success("✅ Empty session ID validation working correctly", "TEST")
                else:
                    raise ValueError(f"Unexpected error message: {ve}")
            
            self.test_results.append(("Session ID Validation", True, None))
            
        except Exception as e:
            console_error(f"❌ Session ID validation test failed: {e}", "TEST")
            self.test_results.append(("Session ID Validation", False, str(e)))
    
    def print_test_results(self):
        """Print comprehensive test results."""
        print("\n" + "="*60)
        print("🧪 Multi-Agent System Test Results")
        print("="*60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, error in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if error:
                print(f"     Error: {error}")
        
        print(f"\nSummary: {passed}/{total} tests passed")
        
        if passed == total:
            console_success(f"🎉 All tests passed! Multi-agent system is working correctly.", "TEST")
        else:
            console_warning(f"⚠️ {total - passed} test(s) failed. Please review the results.", "TEST")
    
    async def run_all_tests(self):
        """Run the complete test suite."""
        console_info("🚀 Starting multi-agent system test suite...", "TEST")
        
        # Setup
        if not await self.setup():
            console_error("❌ Cannot run tests - setup failed", "TEST")
            return
        
        # Run tests
        await self.test_system_status()
        await self.test_agent_routing()
        await self.test_conversation_flow()
        await self.test_reset_functionality()
        await self.test_error_handling()
        await self.test_session_id_validation()
        
        # Print results
        self.print_test_results()

async def main():
    """Main entry point for the test suite."""
    tester = MultiAgentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
    except Exception as e:
        console_error(f"Test suite error: {e}", "TEST")
        sys.exit(1)
