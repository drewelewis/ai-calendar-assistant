from typing import List
from pydantic import BaseModel
from pydantic import Field

class OpenAIModels():

    class Message(BaseModel):
        role: str = Field(..., description="Type of the message, e.g., 'user' or 'assistant' or 'system' or 'tool'")
        content: str = Field(..., description="Content of the message")

    class Messages(BaseModel):
        messages: list["OpenAIModels.Message"] = Field(..., description="List of messages in the chat")

    def __init__(self) -> None:
        self.models = [self.Message, self.Messages]

    # Method to get models
    def models(self) -> List[BaseModel]:
        return self.models
   