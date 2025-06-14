from pydantic import BaseModel, Field
from typing import Optional, List  # <-- Add List here
from datetime import datetime

class PaymentCreate(BaseModel):
    payee: str  # User who receives the money
    amount: float = Field(ge=0)
    # payer will be current_user.username

class PaymentResponse(BaseModel):
    id: str
    payer: str
    payee: str
    amount: float
    method: str
    status: str
    stripe_payment_intent_id: Optional[str]
    created_at: str
    completed_at: Optional[str]

class BalanceDue(BaseModel):
    from_user: str  # The user who owes
    to_user: str  # The user who is owed
    amount: float  # The amount owed

class UserBalance(BaseModel):
    username: str
    owes: float = 0.0  # Total amount user owes others
    owed_by: float = 0.0  # Total amount user is owed by others
    net_balance: float = 0.0  # Positive if owed, negative if owes
    balances_to_settle: List[BalanceDue] = []  # Specific amounts owed/owing to/from others
