#!/usr/bin/env python3
"""Quick test to verify card rendering is working after 1.125.0 deployment"""

import asyncio
import json
import httpx
import os

async def test_api_cards():
    """Test card rendering through the API endpoint"""
    
    # Get API endpoint from environment or use default
    api_url = os.getenv("API_URL", "http://localhost:8000")
    endpoint = f"{api_url}/multi_agent_chat"
    
    print("[TEST] Testing card rendering via API endpoint...")
    print(f"API URL: {endpoint}")
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "message": "show me your cards"
        }
        
        try:
            response = await client.post(endpoint, json=payload)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response keys: {list(result.keys())}")
                
                # Check for cards
                cards = result.get("cards", [])
                message = result.get("response", "")
                
                print(f"\n[Response]")
                print(f"  Message: {message[:100] if message else '(empty)'}")
                print(f"  Cards count: {len(cards)}")
                
                if cards:
                    print(f"\n[Cards]")
                    for i, card in enumerate(cards):
                        card_type = card.get("type", "Unknown")
                        body = card.get("body", [])
                        title = body[0].get("text", "") if body else "No title"
                        print(f"  Card {i+1}: {card_type} - {title}")
                    print(f"\n[SUCCESS] Cards are rendering! ({len(cards)} cards)")
                    return True
                else:
                    print(f"\n[INFO] No cards in response. Response content:")
                    print(message)
                    if "I don't have" in message or "I don't" in message:
                        print("[ISSUE] ProxyAgent is responding in natural language instead of JSON")
                    return False
            else:
                print(f"[ERROR] API returned status {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            print("Make sure the API is running on localhost:8000")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_api_cards())
    exit(0 if success else 1)

