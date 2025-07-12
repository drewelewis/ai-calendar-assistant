from typing import List, Optional
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv(override=True)


class GraphModels():

    class UserModel(BaseModel):
        ObjectId: int = Field(..., description="ID of the user")
        UserPrincipalName: str = Field(..., description="Name of the user")
        DisplayName: str = Field(..., description="Email of the user")
        JobTitle: str = Field(..., description="Job title of the user")
        Department: str = Field(..., description="Department of the user")
        Email: str = Field(..., description="Email of the user")



    # Init above tools and make available
    def __init__(self) -> None:
        self.models = [self.UserModel]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def models(self) -> List[BaseModel]:
        return self.models
