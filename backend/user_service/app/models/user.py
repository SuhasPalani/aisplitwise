# backend/user_service/app/models/user.py

from pydantic import BaseModel, EmailStr # Ensure BaseModel is imported
from datetime import datetime
from typing import Optional, List

# You might have a custom ObjectID type or need to handle it for MongoDB
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        field_schema.update(type="string")

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase): # Assuming this is the class that was failing
    id: Optional[PyObjectId] = None # MongoDB _id
    hashed_password: str
    friends: List[str] = []
    created_at: datetime = datetime.now()

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True
        fields = {"id": {"alias": "_id"}} # Map 'id' to '_id' for MongoDB