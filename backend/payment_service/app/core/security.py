# backend/payment_service/app/core/security.py
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth import CurrentUser # Import CurrentUser from local schemas
from app.core.config import settings # Import settings to get JWT_SECRET_KEY

# This tokenUrl points to the actual login endpoint of the Auth Service
# It's primarily for OpenAPI/Swagger UI documentation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/auth/token") # Adjust port if auth_service isn't 8001

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_email: EmailStr = payload.get("email") # Assuming you put email in the token payload

        if username is None or user_email is None:
            raise credentials_exception

        return CurrentUser(username=username, email=user_email)
    except JWTError:
        raise credentials_exception