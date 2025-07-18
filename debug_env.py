#!/usr/bin/env python3
"""
Environment Variable Debug Test
"""

import os
from dotenv import load_dotenv

print("🔍 Environment Variable Debug")
print("=" * 50)

print("\n1. Before loading .env file:")
key_before = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
print(f"   AZURE_MAPS_SUBSCRIPTION_KEY: {key_before}")

print("\n2. Loading .env file...")
result = load_dotenv()
print(f"   .env loaded successfully: {result}")

print("\n3. After loading .env file:")
key_after = os.environ.get("AZURE_MAPS_SUBSCRIPTION_KEY")
print(f"   AZURE_MAPS_SUBSCRIPTION_KEY: {key_after}")

if key_after:
    print(f"   Key length: {len(key_after)}")
    print(f"   First 10 chars: {key_after[:10]}")
    print(f"   Last 10 chars: {key_after[-10:]}")
else:
    print("   ❌ Key still not found!")

print("\n4. Checking .env file directly:")
try:
    with open('.env', 'r') as f:
        lines = f.readlines()
        for line_num, line in enumerate(lines, 1):
            if 'AZURE_MAPS_SUBSCRIPTION_KEY' in line:
                print(f"   Line {line_num}: {line.strip()}")
                # Extract the value after the =
                if '=' in line:
                    key_value = line.split('=', 1)[1].strip()
                    print(f"   Extracted value length: {len(key_value)}")
                    print(f"   Extracted value starts with: {key_value[:15]}...")
except Exception as e:
    print(f"   ❌ Error reading .env file: {e}")

print("\n5. All environment variables containing 'AZURE_MAPS':")
for key, value in os.environ.items():
    if 'AZURE_MAPS' in key:
        if value:
            print(f"   {key}: {value[:15]}... (length: {len(value)})")
        else:
            print(f"   {key}: Not set")
