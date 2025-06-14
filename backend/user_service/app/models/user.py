from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        field_schema.update(type="string")

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

# IMPORTANT: This MUST match the schema used by auth_service for storing users
class UserInDB(UserBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None) # MongoDB _id
    passwordHash: str # Changed from 'hashed_password' to 'passwordHash' to match Auth Service
    friends: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow) # Use utcnow for timezone awareness

    class Config:
        populate_by_name = True # Pydantic v2 setting, replaces allow_population_by_field_name
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}