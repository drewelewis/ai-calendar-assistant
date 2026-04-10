"""
Clear chat messages for a specific session
"""
import requests
import json

# API endpoint
API_URL = "https://aiwrapper-private.blackwater-1d9c013c.eastus2.azurecontainerapps.io"

# Session ID from recent tests
SESSION_ID = "69149650-b87e-44cf-9413-db5c1a5b6d3f"

def clear_messages(session_id: str):
    """Clear chat history for a session"""
    url = f"{API_URL}/clear_chat_history"
    payload = {
        "session_id": session_id
    }
    
    print(f"🗑️  Clearing messages for session: {session_id}")
    print(f"📡 Calling: {url}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Response: {json.dumps(result, indent=2)}")
        
        if result.get("status") == "success":
            print(f"✅ Chat history cleared successfully!")
        else:
            print(f"⚠️  Unexpected response: {result}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error clearing messages: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    clear_messages(SESSION_ID)
