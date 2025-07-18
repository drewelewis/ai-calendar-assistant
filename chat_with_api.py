# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
import json
import uuid
from typing import Annotated
import datetime
import aiohttp
import colorama
from dotenv import load_dotenv

load_dotenv()
CHAT_SESSION_ID = os.getenv("CHAT_SESSION_ID")
# exit if chat session ID is not set
if not CHAT_SESSION_ID:
    raise ValueError("CHAT_SESSION_ID environment variable is not set")

async def main():
    while True:
        # Call localhost:/8989/api/chat_agent with a user input
        user_input = input("Enter your message (or 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8989/agent_chat",
                json={
                    "session_id": CHAT_SESSION_ID,
                    "message": user_input
                    }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Response: {data.get('response', 'No response')}")
                else:
                    print(f"Error: {response.status} - {await response.text()}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR RUNNING MAIN: {type(e).__name__}: {e}")