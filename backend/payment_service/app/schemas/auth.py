# backend/payment_service/app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class CurrentUser(BaseModel):
    username: str
    email: EmailStr
    # Add any other fields you expect from the token payload (e.g., user_id)