import asyncio
import aiohttp
import os
from typing import Dict, Any, Optional

# Import telemetry components
from telemetry.console_output import console_warning, console_telemetry_event

# Imports for chat messages
from semantic_kernel.contents import ChatMessageContent, AuthorRole

class ThreadUtilities:
    """Utility class for Microsoft Teams operations."""
    
    def __init__(self):
        """
        Initialize ThreadUtilities.
        """
        pass

    async def ensure_system_and_instruction_messages(self, thread, session_id, prompts, logger):
        """
        Ensure the thread contains a SYSTEM message and the instruction USER message.
        Handles async iterators, lists, and different thread APIs.

        Args:
            thread: thread object to inspect/mutate
            session_id: session identifier for prompts
            prompts: prompts module exposing system_message() and instructions()
            logger: logger for debug/warning/error
            
        Returns:
            thread: The modified thread object (for method chaining and clarity)
        """
        has_system_message = False
        messages = []

        try:
            # Support multiple thread shapes
            if hasattr(thread, "_chat_history") and hasattr(thread._chat_history, "messages"):
                messages = thread._chat_history.messages
            elif hasattr(thread, "messages"):
                if hasattr(thread.messages, "__aiter__"):
                    async for msg in thread.messages:
                        messages.append(msg)
                elif hasattr(thread.messages, "__iter__"):
                    messages = list(thread.messages)
                else:
                    messages = thread.messages

            def _is_system_role(role):
                if role is None:
                    return False
                try:
                    if role == AuthorRole.SYSTEM:
                        return True
                except Exception:
                    pass
                if isinstance(role, str) and role.strip().lower() == "system":
                    return True
                if hasattr(role, "name") and getattr(role, "name").upper() == "SYSTEM":
                    return True
                return False

            if any(_is_system_role(getattr(msg, "role", None)) for msg in messages):
                logger.debug("Found existing system message in thread")
                has_system_message = True
            else:
                logger.debug("No existing system message found in thread")
                has_system_message = False

        except Exception as e:
            logger.debug(f"Could not check existing messages: {e}")
            has_system_message = False

        if not has_system_message:
            def add_message_to_thread(message, message_type):
                try:
                    if hasattr(thread, "add_chat_message"):
                        thread.add_chat_message(message)
                        logger.debug(f"Added {message_type} using add_chat_message")
                    elif hasattr(thread, "add_message"):
                        thread.add_message(message)
                        logger.debug(f"Added {message_type} using add_message")
                    elif hasattr(thread, "_chat_history") and hasattr(thread._chat_history, "add_message"):
                        thread._chat_history.add_message(message)
                        logger.debug(f"Added {message_type} using _chat_history.add_message")
                    elif hasattr(thread, "_chat_history") and hasattr(thread._chat_history, "messages"):
                        thread._chat_history.messages.append(message)
                        logger.debug(f"Added {message_type} by appending to messages list")
                    else:
                        logger.warning(f"Could not find method to add {message_type} to thread")
                except Exception as e:
                    logger.error(f"Failed to add {message_type} to thread: {e}")

            try:
                system_message = ChatMessageContent(
                    role=AuthorRole.SYSTEM,
                    content=prompts.system_message(session_id)
                )
                add_message_to_thread(system_message, "system message")
            except Exception as e:
                logger.error(f"Failed to construct/add system message: {e}")

            try:
                instruction_message = ChatMessageContent(
                    role=AuthorRole.USER,
                    content=prompts.instructions(session_id)
                )
                add_message_to_thread(instruction_message, "instruction message")
            except Exception as e:
                logger.error(f"Failed to construct/add instruction message: {e}")

        return thread
