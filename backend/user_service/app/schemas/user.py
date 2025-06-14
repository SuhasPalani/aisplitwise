from pydantic import BaseModel, Field
from typing import List, Optional

class UserSearch(BaseModel):
    username: str
    email: str

class FriendRequest(BaseModel):
    username: str

class FriendStatus(BaseModel):
    message: str
    friends: List[str]

class UserProfile(BaseModel):
    username: str
    email: str
    friends: List[str]
    created_at: str # Will be formatted as string for simplicity