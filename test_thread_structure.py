#!/usr/bin/env python3

"""
Simple test script to understand the ChatHistoryAgentThread structure
"""

import asyncio
from semantic_kernel.agents import ChatHistoryAgentThread
from semantic_kernel.contents import ChatMessageContent, AuthorRole

async def test_thread_structure():
    try:
        # Create a thread
        thread = ChatHistoryAgentThread()
        print("✅ Thread created successfully")
        
        # Check attributes
        print(f"Thread attributes: {[attr for attr in dir(thread) if not attr.startswith('__')]}")
        
        # Check for _chat_history
        if hasattr(thread, '_chat_history'):
            print("✅ Thread has _chat_history attribute")
            chat_history = thread._chat_history
            print(f"Chat history type: {type(chat_history)}")
            print(f"Chat history attributes: {[attr for attr in dir(chat_history) if not attr.startswith('__')]}")
            
            # Check for messages
            if hasattr(chat_history, 'messages'):
                print("✅ Chat history has messages attribute")
                print(f"Messages type: {type(chat_history.messages)}")
                print(f"Initial messages count: {len(chat_history.messages)}")
            
            # Try creating a message and adding it
            try:
                message = ChatMessageContent(
                    role=AuthorRole.USER,
                    content="Test message"
                )
                print(f"✅ Created message: {message}")
                
                # Try different ways to add the message
                if hasattr(chat_history, 'add_message'):
                    chat_history.add_message(message)
                    print("✅ Added message using add_message method")
                elif hasattr(chat_history, 'messages'):
                    chat_history.messages.append(message)
                    print("✅ Added message by appending to messages list")
                    print(f"Messages count after adding: {len(chat_history.messages)}")
                else:
                    print("❌ No known way to add message")
                    
            except Exception as e:
                print(f"❌ Error creating/adding message: {e}")
        else:
            print("❌ Thread does not have _chat_history attribute")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_thread_structure())
