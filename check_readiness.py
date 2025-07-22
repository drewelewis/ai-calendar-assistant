#!/usr/bin/env python3
"""
Simple multi-agent readiness check focused on Risk Agent
"""
import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("📄 .env file loaded")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables")

def check_environment():
    """Check required environment variables."""
    required_vars = [
        'OPENAI_ENDPOINT',
        'OPENAI_API_KEY', 
        'OPENAI_MODEL_DEPLOYMENT_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def check_imports():
    """Check if all required modules can be imported."""
    try:
        from ai.multi_agent import MultiAgentOrchestrator
        print("✅ MultiAgentOrchestrator imports successfully")
        
        from plugins.risk_plugin import RiskPlugin
        print("✅ RiskPlugin imports successfully")
        
        from operations.risk_operations import RiskOperations
        print("✅ RiskOperations imports successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def check_risk_data():
    """Check if risk data is available."""
    try:
        from operations.risk_operations import RiskOperations
        
        risk_ops = RiskOperations()
        clients = risk_ops._mock_client_data
        
        print(f"✅ Risk operations initialized with {len(clients)} mock clients:")
        for client_id, data in clients.items():
            print(f"   - {client_id}: {data['client_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk data check failed: {e}")
        return False

def main():
    """Run all readiness checks."""
    print("🔍 Multi-Agent System Readiness Check")
    print("=" * 40)
    
    checks = [
        ("Environment Variables", check_environment),
        ("Module Imports", check_imports), 
        ("Risk Data", check_risk_data)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n🧪 Checking {check_name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 READY: Multi-agent system with Risk Agent is ready!")
        print("\nKey components verified:")
        print("✅ Environment configuration")
        print("✅ Multi-agent orchestrator")
        print("✅ Risk plugin and operations")
        print("✅ Mock client data (LCOLE, MERIDIAN, QUANTUM)")
        print("\nThe system can handle risk-related queries through:")
        print("  - /agent_chat endpoint (single agent)")
        print("  - /multi_agent_chat endpoint (multi-agent with specialized routing)")
        return 0
    else:
        print("❌ NOT READY: Some components have issues!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
