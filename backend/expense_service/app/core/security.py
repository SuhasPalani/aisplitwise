# backend/expense_service/app/core/security.py
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os

# Load environment variables (ensure .env is copied to /app in Dockerfile)
load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256") # Default to HS256

# You'll also need CurrentUser and some parts of auth schema from auth_service
# It's best to put these in a shared library or duplicate them *if* they are truly simple DTOs.
# For now, let's copy them directly into expense_service's schemas/auth.py for quick fix.

# Assuming CurrentUser is defined like this in auth_service/app/schemas/auth.py
class CurrentUser(BaseModel):
    username: str
    email: EmailStr
    # Add any other fields you expect from the token payload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token") # This URL points to auth_service

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_email: EmailStr = payload.get("email") # Assuming email is also in token
        if username is None or user_email is None:
            raise credentials_exception
        # You might fetch the user from your local DB here if you need more user details
        # For simplicity, we assume username and email are enough from the token
        return CurrentUser(username=username, email=user_email)
    except JWTError:
        raise credentials_exception