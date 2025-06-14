from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId

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

class ExpenseInDB(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    group_id: PyObjectId
    amount: float = Field(ge=0)
    paid_by: str # Username
    participants: List[str] # Usernames
    description: str
    split: Dict[str, float] = {} # Computed by AI. Key: username, Value: amount
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # status: str = "pending_split" # Could add status to track AI processing

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}