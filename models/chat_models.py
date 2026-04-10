from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pydantic import Field

class ChatModels():

    class AdaptiveCardAction(BaseModel):
        """Represents a button submission from an Adaptive Card in Teams"""
        action: str = Field(..., description="Action identifier from card button")
        data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data from card submission")

    class Message(BaseModel):
        session_id: str = Field(..., description="Unique identifier for the chat session")
        message: str = Field(..., description="Content of the message")
        user_timezone: Optional[str] = Field(default=None, description="IANA timezone of the logged-in user (e.g. 'America/New_York', 'America/Chicago', 'America/Los_Angeles') — defaults to UTC if not provided")
        user_local_timestamp: Optional[str] = Field(default=None, description="User's current local timestamp with UTC offset (e.g. '2026-03-10T14:30:00-05:00') — from activity.localTimestamp")
        user_locale: Optional[str] = Field(default=None, description="User's locale (e.g. 'en-US') — from activity.locale")
        card_action: Optional["AdaptiveCardAction"] = Field(default=None, description="Optional card action from Teams card button")
    
    class Session(BaseModel):
        session_id: str = Field(..., description="Unique identifier for the chat session")

    class ChatResponse(BaseModel):
        """Multi-agent chat response with optional Adaptive Cards"""
        response: str = Field(..., description="Text response from the AI")
        card: Optional[Dict[str, Any]] = Field(default=None, description="Optional single Adaptive Card")
        cards: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional list of Adaptive Cards")
        session_id: Optional[str] = Field(default=None, description="Session ID for tracking")

    def __init__(self) -> None:
        self.models = [self.Message, self.ChatResponse]

    # Method to get models
    def models(self) -> List[BaseModel]:
        return self.models
   