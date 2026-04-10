#!/usr/bin/env python3
"""Simple test of the card rendering via API"""

import requests
import json

api_url = "https://aiwrapper.azurecontainerapps.io/multi_agent_chat"

print("[TEST] Calling production API with 'show me your cards'")
print(f"URL: {api_url}")
print("-" * 60)

try:
    response = requests.post(api_url, json={"message": "show me your cards"}, timeout=15)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        cards = data.get("cards", [])
        msg = data.get("response", "")
        
        print(f"Cards: {len(cards)}")
        print(f"Message length: {len(msg)}")
        print(f"Message preview: {msg[:150]}")
        
        if cards:
            print(f"\n[SUCCESS] Got {len(cards)} cards!")
            for i, card in enumerate(cards):
                body = card.get("body", [])
                title = body[0].get("text", "") if body else ""
                print(f"  Card {i+1}: {title}")
        else:
            print(f"\n[INFO] No cards returned")
            if "I don't" in msg or "cannot" in msg.lower():
                print("  -> ProxyAgent is NOT returning JSON with cards")
    else:
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"Error: {e}")
