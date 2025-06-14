from pydantic import BaseModel, Field
from typing import List, Optional

class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    # Members will be added via separate endpoint or default to creator

class GroupResponse(BaseModel):
    id: str
    name: str
    members: List[str]
    created_at: str
    created_by: str

class AddRemoveMembers(BaseModel):
    usernames: List[str]

class MemberStatus(BaseModel):
    message: str
    group_name: str
    members: List[str]