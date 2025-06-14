# backend/expense_service/app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class CurrentUser(BaseModel):
    """
    Schema representing the current authenticated user.
    This is typically derived from a JWT token's payload.
    """
    username: str
    email: EmailStr
    # Add any other fields that are consistently present in the JWT payload
    # and are needed by this service to identify/authorize the user.
    # For instance, if user IDs are in the token:
    # user_id: str