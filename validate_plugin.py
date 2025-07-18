#!/usr/bin/env python3
"""Simple validation test for the Graph Plugin"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from plugins.graph_plugin import GraphPlugin
    print("✅ Graph Plugin import successful")
    
    # Initialize plugin
    plugin = GraphPlugin(debug=True, session_id="validation-test")
    print("✅ Plugin initialization successful")
    
    # Check if our new method exists
    if hasattr(plugin, 'get_user_location'):
        print("✅ get_user_location method found in plugin")
    else:
        print("❌ get_user_location method NOT found in plugin")
    
    # List all user-related methods
    user_methods = [method for method in dir(plugin) if method.startswith('get_user')]
    print(f"📋 Available user methods: {user_methods}")
    
    print("\n🎉 Validation completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
