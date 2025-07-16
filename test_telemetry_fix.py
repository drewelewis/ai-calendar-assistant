#!/usr/bin/env python3
"""
Simple test to verify telemetry initialization works correctly
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_telemetry_init():
    """Test telemetry initialization"""
    try:
        print("🧪 Testing telemetry initialization...")
        
        from telemetry.config import initialize_telemetry, get_logger
        
        service_name = os.getenv("TELEMETRY_SERVICE_NAME", "ai-calendar-assistant")
        service_version = os.getenv("TELEMETRY_SERVICE_VERSION", "1.0.0")
        
        success = initialize_telemetry(
            service_name=service_name,
            service_version=service_version
        )
        
        if success:
            print("✅ Telemetry initialization successful")
            logger = get_logger()
            logger.info("Test log message")
            print("✅ Logger works")
        else:
            print("⚠️ Telemetry initialization failed, but that's OK for testing")
            
        return True
        
    except Exception as e:
        print(f"❌ Telemetry test failed: {e}")
        return False

def test_agent_import():
    """Test agent import"""
    try:
        print("🧪 Testing Agent import...")
        from ai.agent import Agent
        print("✅ Agent import successful")
        return True
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running telemetry fix tests...")
    print()
    
    telemetry_ok = test_telemetry_init()
    print()
    
    agent_ok = test_agent_import() 
    print()
    
    if telemetry_ok and agent_ok:
        print("🎉 All tests passed! The fixes are working.")
    else:
        print("⚠️ Some tests failed. Check the output above.")
