"""
Simple test for console output
"""

import os

# Set configuration for testing
os.environ['TELEMETRY_CONSOLE_ENABLED'] = 'true'
os.environ['TELEMETRY_CONSOLE_LEVEL'] = 'INFO'
os.environ['TELEMETRY_CONSOLE_COLORS'] = 'true'

from telemetry.console_output import console_info, console_token_usage, console_telemetry_event

print("Testing console output...")

console_info("Application starting")
console_telemetry_event("test_event", {"key": "value"})
console_token_usage("gpt-4o", 100, 50, 0.005, "test")

print("Console output test completed!")
