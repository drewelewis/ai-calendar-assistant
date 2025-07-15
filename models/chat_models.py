from typing import List
from pydantic import BaseModel
from pydantic import Field

class ChatModels():

    class Message(BaseModel):
        session_id: str = Field(..., description="Type of the message, e.g., 'user' or 'assistant' or 'system' or 'tool'")
        message: str = Field(..., description="Content of the message")


    def __init__(self) -> None:
        self.models = [self.Message]

    # Method to get models
    def models(self) -> List[BaseModel]:
        return self.models
   