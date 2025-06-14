from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        field_schema.update(type="string")

class UserInDB(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None) # MongoDB _id
    email: EmailStr
    username: str
    passwordHash: str # IMPORTANT: Ensure this matches the field in your DB and auth.py
    friends: List[str] = [] # Storing usernames of friends, for simplicity
    created_at: datetime = Field(default_factory=datetime.utcnow) # Use utcnow for timezone awareness

    class Config:
        populate_by_name = True # Pydantic v2 setting, replaces allow_population_by_field_name
        arbitrary_types_allowed = True # For PyObjectId
        json_encoders = {ObjectId: str} # This will allow us to convert BSON ObjectId to string for JSON output