from typing import List
from pydantic import BaseModel
from pydantic import Field

class ChatModels():

    class Message(BaseModel):
        session_id: str = Field(..., description="Unique identifier for the chat session")
        message: str = Field(..., description="Content of the message")
    
    class Session(BaseModel):
        session_id: str = Field(..., description="Unique identifier for the chat session")




    def __init__(self) -> None:
        self.models = [self.Message]

    # Method to get models
    def models(self) -> List[BaseModel]:
        return self.models
   