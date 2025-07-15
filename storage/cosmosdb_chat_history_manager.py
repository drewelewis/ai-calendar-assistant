import os
import datetime
import uuid

from identity.azure_credentials import AzureCredentials
from azure.cosmos import CosmosClient, PartitionKey
from azure.core.exceptions import ClientAuthenticationError


class CosmosDBChatHistoryManager:
    """Manages chat history persistence with Azure Cosmos DB using Azure Identity or connection key."""
    
    def __init__(self, endpoint, database_name, container_name, credential=None):
        """
        Initialize the CosmosDB client using Azure Identity or connection key as fallback.
        
        Args:
            endpoint: CosmosDB endpoint URL
            database_name: Name of the database
            container_name: Name of the container
            credential: Optional Azure credential. If None, uses get_azure_credential()
        """
        import logging
        logger = logging.getLogger(__name__)
        
        self.client = None
        
        # Try Azure Identity first if no credential provided
        if credential is None:
            try:
                logger.info("🔑 Attempting Azure Identity authentication for CosmosDB...")
                logger.info(f"🌐 Connecting to CosmosDB URL: {endpoint}")
                print(f"🌐 Connecting to CosmosDB URL: {endpoint}")  # Also print to console
                
                credential = AzureCredentials.get_credential()
                self.client = CosmosClient(endpoint, credential=credential)
                logger.info("✅ Connected to CosmosDB using Azure Identity")
                
                # Test the connection by attempting to read databases
                try:
                    list(self.client.list_databases())
                    logger.info("✅ CosmosDB connection verified successfully")
                except Exception as test_error:
                    logger.error(f"❌ CosmosDB connection test failed: {test_error}")
                    raise test_error
                    
            except Exception as e:
                logger.warning(f"⚠ Azure Identity authentication failed: {e}")
                print(f"⚠ Azure Identity failed for URL: {endpoint}")  # Also print to console
                
                # Check if this is a managed identity issue in production
                if "ManagedIdentityCredential" in str(e) or "No managed identity endpoint found" in str(e):
                    logger.error("🚨 Managed Identity authentication failed - this usually indicates:")
                    logger.error("   1. Managed Identity is not enabled on this Azure resource")
                    logger.error("   2. Managed Identity doesn't have proper permissions on CosmosDB")
                    logger.error("   3. Running outside of Azure environment without proper configuration")
                
                # Fall back to connection key if available
                cosmos_key = os.getenv("COSMOS_KEY")
                if cosmos_key:
                    try:
                        logger.info("🔄 Falling back to connection key authentication...")
                        logger.info(f"🌐 Retry connecting to CosmosDB URL: {endpoint}")
                        print(f"🔄 Retrying with connection key for URL: {endpoint}")  # Also print to console
                        
                        self.client = CosmosClient(endpoint, cosmos_key)
                        logger.info("✅ Connected to CosmosDB using connection key")
                        
                        # Test the connection
                        list(self.client.list_databases())
                        logger.info("✅ CosmosDB connection verified with connection key")
                        
                    except Exception as key_error:
                        logger.error(f"❌ Connection key authentication also failed: {key_error}")
                        print(f"❌ Connection key also failed for URL: {endpoint}")  # Also print to console
                        raise ClientAuthenticationError(
                            f"Failed to connect with both Azure Identity and connection key. "
                            f"Azure Identity error: {e}. Connection key error: {key_error}"
                        )
                else:
                    logger.error("❌ No COSMOS_KEY environment variable found for fallback")
                    raise ClientAuthenticationError(
                        f"Azure Identity failed and no connection key available. "
                        f"Error: {e}. Please either:\n"
                        f"1. Fix managed identity configuration, or\n"
                        f"2. Set COSMOS_KEY environment variable"
                    )
        else:
            # Use provided credential
            logger.info(f"🌐 Connecting to CosmosDB with provided credential: {endpoint}")
            print(f"🌐 Connecting to CosmosDB with provided credential: {endpoint}")  # Also print to console
            self.client = CosmosClient(endpoint, credential=credential)
            logger.info("✅ Connected to CosmosDB using provided credential")
        
        # Initialize database and container
        try:
            self.database = self.client.create_database_if_not_exists(id=database_name)
            self.container = self.database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path="/sessionId"),
                offer_throughput=400  # Minimum throughput
            )
            logger.info(f"✅ CosmosDB database '{database_name}' and container '{container_name}' ready")
        except Exception as setup_error:
            logger.error(f"❌ Failed to setup CosmosDB database/container: {setup_error}")
            raise
    
    async def save_chat_history(self, thread, session_id=None):
        """Save chat history from a thread to Cosmos DB."""
        if not thread:
            return
        
        # Generate a session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Extract messages from thread
        messages = []
        
        # Get the chat history from the thread
        try:
            # Handle different ways to access messages in Semantic Kernel
            thread_messages = []
            
            # Check if thread has messages attribute or property
            if hasattr(thread, 'messages'):
                # Handle async generator case
                if hasattr(thread.messages, '__aiter__'):
                    async_messages = thread.messages
                    async for message in async_messages:
                        thread_messages.append(message)
                else:
                    thread_messages = thread.messages
            # Try get_messages method
            elif hasattr(thread, 'get_messages'):
                get_messages_result = thread.get_messages()
                # Check if it's an async generator
                if hasattr(get_messages_result, '__aiter__'):
                    async for message in get_messages_result:
                        thread_messages.append(message)
                else:
                    thread_messages = get_messages_result
            # Try other possible attributes
            elif hasattr(thread, 'chat_history'):
                thread_messages = thread.chat_history
            elif hasattr(thread, 'history'):
                thread_messages = thread.history
            # Check if thread is dict-like with messages key
            elif isinstance(thread, dict) and "messages" in thread:
                thread_messages = thread["messages"]
                
            # Process all collected messages
            for message in thread_messages:
                if message.role.value == "user":
                    role = "user"
                elif message.role.value == "assistant":
                    role = "assistant"
                elif message.role.value == "system":
                    role = "system"
            
                # Enhanced content with function call details for CosmosDB storage
                # enhanced_content = self._create_enhanced_message_content(message)
                if hasattr(message, 'content'):
                    if message.content != "":
                        messages.append({
                            "role": role,
                            "content": message.content,
                            "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
                        })

        except Exception as e:
            print(f"Warning: Could not extract messages from thread: {e}")
            # Continue with an empty messages list
            
        # Create document to store
        chat_history_document = {
            "id": str(uuid.uuid4()),
            "sessionId": session_id,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "messages": messages
        }
        
        # Save to Cosmos DB
        try:
            self.container.create_item(body=chat_history_document)
            return session_id
        except Exception as e:
            print(f"Error saving chat history to CosmosDB: {e}")
            # Re-raise the exception so calling code can handle it
            raise
        
    async def load_chat_history(self, session_id):
        """Load chat history from Cosmos DB and return the raw messages."""
        try:
            query = f"SELECT * FROM c WHERE c.sessionId = '{session_id}' ORDER BY c.timestamp DESC"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            
            if not items:
                print(f"No chat history found for session ID: {session_id}")
                return None
                
            # Take the most recent chat history
            chat_history = items[0]
            messages = chat_history.get("messages", [])
            
            print(f"Loaded chat history with {len(messages)} messages from {chat_history.get('timestamp', 'unknown time')}")
            
            # Return the raw messages - thread recreation will be handled by the calling code
            return messages
        except Exception as e:
            print(f"Error loading chat history from CosmosDB: {e}")
            return None
        
    async def create_hydrated_thread(self, kernel, session_id):
        """
        Create a new ChatHistoryAgentThread and hydrate it with messages from CosmosDB.
        
        Args:
            kernel: The Semantic Kernel instance
            session_id: The session ID to load chat history for
            
        Returns:
            ChatHistoryAgentThread: A new thread with loaded messages, or empty thread if loading fails
        """
        from semantic_kernel.agents import ChatHistoryAgentThread
        from semantic_kernel.contents import ChatMessageContent, AuthorRole
        
        # Debug mode setting
        debug_mode = os.getenv("DEBUG_THREAD_API", "false").lower() == "true"
        
        # Create a new thread
        thread = ChatHistoryAgentThread()
        
        # Debug: Print available methods on the thread to understand the API
        if debug_mode:
            thread_methods = [method for method in dir(thread) if not method.startswith('_')]
            print(f"Available thread methods: {thread_methods}")
            if hasattr(thread, '_chat_history'):
                chat_history_methods = [method for method in dir(thread._chat_history) if not method.startswith('_')]
                print(f"Available chat_history methods: {chat_history_methods}")
        
        try:
            # Load previous messages
            previous_messages = await self.load_chat_history(session_id)
            if not previous_messages:
                return thread
            
            print(f"Hydrating thread with {len(previous_messages)} messages...")
            
            # Debug: Show what kind of thread we have
            if debug_mode:
                print(f"Thread type: {type(thread).__name__}")
            
            # Create ChatMessageContent objects and add them to the thread
            message_count = 0
            for i, stored_message in enumerate(previous_messages):
                try:
                    role = stored_message.get("role", "user")
                    content = stored_message.get("content", "")
                    timestamp = stored_message.get("timestamp", "unknown")
                    
                    # Skip empty messages
                    if not content.strip():
                        continue
                    
                    # Map role to AuthorRole
                    if role == "user":
                        author_role = AuthorRole.USER
                        print(f"  Adding user message {i+1}: {content[:50]}...")
                    elif role == "assistant":
                        author_role = AuthorRole.ASSISTANT
                        print(f"  Adding assistant message {i+1}: {content[:50]}...")
                    elif role == "system":
                        author_role = AuthorRole.SYSTEM
                        print(f"  Adding system message {i+1}: {content[:50]}...")
                    else:
                        print(f"  Unknown message role '{role}', skipping message")
                        continue
                    
                    # Create a ChatMessageContent object
                    message = ChatMessageContent(
                        role=author_role,
                        content=content
                    )
                    
                    # Add the message to the thread using the proper API
                    try:
                        # Use add_chat_message if available (newer API)
                        if hasattr(thread, 'add_chat_message'):
                            thread.add_chat_message(message)
                            message_count += 1
                        # Fallback to add_message if available
                        elif hasattr(thread, 'add_message'):
                            thread.add_message(message)
                            message_count += 1
                        # Try accessing the chat history and add message there
                        elif hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'add_message'):
                            thread._chat_history.add_message(message)
                            message_count += 1
                        elif hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'messages'):
                            # If there's a messages list, append directly
                            thread._chat_history.messages.append(message)
                            message_count += 1
                        else:
                            print(f"  Unable to add message to thread - unknown chat history structure")
                    except Exception as msg_error:
                        print(f"  Error adding message to thread: {msg_error}")
                        # Try the direct approach as a last resort
                        try:
                            if hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'messages'):
                                thread._chat_history.messages.append(message)
                                message_count += 1
                        except Exception as fallback_error:
                            print(f"  Fallback approach also failed: {fallback_error}")
                        
                except Exception as e:
                    print(f"  Failed to add message {i+1} to thread: {e}")
                    if debug_mode:
                        print(f"  Message that failed: role={role}, content={content[:100]}...")
                        print(f"  Exception type: {type(e).__name__}")
                    continue
            
            print(f"Successfully hydrated thread with {message_count} messages")
            
            # Validate the hydration worked
            if debug_mode and message_count > 0:
                try:
                    # Try to verify messages were actually added
                    if hasattr(thread, '_chat_history') and hasattr(thread._chat_history, 'messages'):
                        actual_count = len(thread._chat_history.messages)
                        print(f"Verification: Thread now contains {actual_count} messages")
                    elif hasattr(thread, 'messages'):
                        # Handle async generator case
                        if hasattr(thread.messages, '__aiter__'):
                            count = 0
                            async for _ in thread.messages:
                                count += 1
                            print(f"Verification: Thread now contains {count} messages")
                        else:
                            actual_count = len(thread.messages) if hasattr(thread.messages, '__len__') else "unknown"
                            print(f"Verification: Thread now contains {actual_count} messages")
                except Exception as verify_error:
                    print(f"Could not verify thread hydration: {verify_error}")
            
            return thread
            
        except Exception as e:
            print(f"Error hydrating thread: {e}")
            print("Returning empty thread")
            return thread
