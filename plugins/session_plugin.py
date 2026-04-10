# Copyright (c) Microsoft. All rights reserved.
from typing import Annotated

from semantic_kernel.functions import kernel_function


class SessionPlugin:
    """Provides session management operations as kernel functions."""

    def __init__(self, session_id: str, cosmos_manager=None):
        self._session_id = session_id
        self._cosmos_manager = cosmos_manager

    @kernel_function(
        description="""
        Clear the chat history and start a fresh conversation.

        CALL THIS WHEN the user says ANY of:
        - "new", "new chat", "new session"
        - "start over", "fresh start", "begin again", "restart"
        - "clear chat", "clear history", "clear everything"
        - "reset", "wipe history", "forget everything"

        No parameters needed — uses the current session automatically.
        Returns a confirmation message indicating the history has been cleared.
        """
    )
    async def clear_chat_history(self) -> Annotated[str, "Confirmation that chat history was cleared"]:
        try:
            if self._cosmos_manager:
                await self._cosmos_manager.clear_chat_history(session_id=self._session_id)
            return "Chat history cleared! Starting fresh — how can I help you today?"
        except Exception as e:
            return f"Could not clear history: {e}"
