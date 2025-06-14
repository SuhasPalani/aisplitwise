from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ExpenseCreate(BaseModel):
    group_id: str
    amount: float = Field(ge=0)
    # paid_by will be current_user.username
    participants: List[str] # Usernames who are part of this expense
    description: str

class ExpenseResponse(BaseModel):
    id: str
    group_id: str
    amount: float
    paid_by: str
    participants: List[str]
    description: str
    split: Dict[str, float] # username -> amount
    created_at: str

class ExpenseUpdateSplit(BaseModel):
    split: Dict[str, float]