import asyncio
import aiohttp
import os
from typing import Dict, Any, Optional

# Import telemetry components
from telemetry.console_output import console_warning, console_telemetry_event

class TeamsUtilities:
    """Utility class for Microsoft Teams operations."""
    
    def __init__(self):
        """
        Initialize TeamsUtilities.
        """
        self.direct_message_url = os.getenv("TEAMS_DIRECT_MESSAGE_URL")
        
        # Check if direct message URL is configured
        if not self.direct_message_url:
            console_warning(
                "Teams direct messaging won't be enabled - TEAMS_DIRECT_MESSAGE_URL environment variable is missing",
                "teams_utilities"
            )
            console_telemetry_event(
                "teams_config_missing",
                {
                    "missing_config": "TEAMS_DIRECT_MESSAGE_URL",
                    "impact": "direct_messaging_disabled"
                },
                "teams_utilities"
            )
    
    async def send_message_fire_and_forget(self, message_data: Dict[str, Any], user_id: str) -> None:
        """
        Send a message to Teams without waiting for response.
        
        Args:
            message_data: Dictionary containing the message payload
            user_id: Target user ID for the message
        """
        if not self.direct_message_url:
            raise ValueError("Direct message URL not configured")
        
        # Create payload with correct structure
        payload = {
            "user_id": user_id,
            "message": message_data.get("message", "")
        }
        # Fire-and-forget: do not await the response
        asyncio.create_task(self._async_post(self.direct_message_url, payload))
    
    async def _async_post(self, url: str, data: Dict[str, Any]) -> None:
        """
        Internal method to perform async POST request.
        
        Args:
            url: Target URL
            data: JSON payload to send
        """
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=data)
        except Exception:
            # Silently ignore errors in fire-and-forget mode
            pass