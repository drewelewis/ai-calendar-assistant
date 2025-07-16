#!/usr/bin/env python3
"""
Debug script to find the source of pkg_resources import
"""

import warnings
import sys
import traceback

# Capture all warnings
warnings.filterwarnings('error', message='.*pkg_resources.*')

def trace_imports():
    """Trace imports to find pkg_resources usage"""
    original_import = __builtins__.__import__
    
    def custom_import(name, *args, **kwargs):
        if 'pkg_resources' in name:
            print(f"🔍 Found pkg_resources import: {name}")
            traceback.print_stack()
            print("-" * 50)
        return original_import(name, *args, **kwargs)
    
    __builtins__.__import__ = custom_import

def main():
    """Main debug function"""
    print("🐛 Starting pkg_resources debugging...")
    
    # Enable import tracing
    trace_imports()
    
    try:
        # Try importing telemetry first
        print("📦 Importing telemetry...")
        from telemetry.config import initialize_telemetry
        print("✅ Telemetry imported successfully")
        
        # Try importing other modules
        print("📦 Importing azure-monitor-opentelemetry...")
        from azure.monitor.opentelemetry import configure_azure_monitor
        print("✅ Azure Monitor OpenTelemetry imported successfully")
        
        # Try importing OpenTelemetry components
        print("📦 Importing OpenTelemetry components...")
        from opentelemetry import trace, metrics
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        print("✅ OpenTelemetry components imported successfully")
        
        # Try importing Semantic Kernel
        print("📦 Importing Semantic Kernel...")
        try:
            from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
            print("✅ Semantic Kernel imported successfully")
        except ImportError as e:
            print(f"⚠️ Semantic Kernel import failed: {e}")
        
    except DeprecationWarning as e:
        print(f"🚨 DeprecationWarning caught: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
