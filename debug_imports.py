#!/usr/bin/env python3
"""
Debug script to test OpenTelemetry imports
"""

print("Starting import tests...")

try:
    print("1. Testing basic OpenTelemetry imports...")
    from opentelemetry import trace, metrics
    print("✅ Basic OpenTelemetry imports successful")
except Exception as e:
    print(f"❌ Basic OpenTelemetry imports failed: {e}")

try:
    print("2. Testing logging instrumentation...")
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    print("✅ Logging instrumentation import successful")
except Exception as e:
    print(f"❌ Logging instrumentation import failed: {e}")

try:
    print("3. Testing azure core instrumentation... (SKIPPED - not required)")
    # from opentelemetry.instrumentation.azure_core import AzureCoreInstrumentor
    print("✅ Azure core instrumentation import skipped (not available)")
except Exception as e:
    print(f"❌ Azure core instrumentation import failed: {e}")

try:
    print("4. Testing azure monitor...")
    from azure.monitor.opentelemetry import configure_azure_monitor
    print("✅ Azure monitor import successful")
except Exception as e:
    print(f"❌ Azure monitor import failed: {e}")

try:
    print("5. Testing telemetry module...")
    from telemetry import initialize_telemetry
    print("✅ Telemetry module import successful")
except Exception as e:
    print(f"❌ Telemetry module import failed: {e}")

print("Import tests completed.")
