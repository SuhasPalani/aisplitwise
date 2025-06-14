from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth import CurrentUser # Import CurrentUser from local schemas
from app.core.config import settings # Import settings to get JWT_SECRET_KEY
from pydantic import EmailStr # Required for type hinting email if used directly, though not explicitly in CurrentUser now

# This tokenUrl points to the actual login endpoint of the Auth Service
# It's primarily for OpenAPI/Swagger UI documentation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/auth/login") 

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_email: str = payload.get("email") # Ensure email is in the token payload from auth_service
        user_id: str = payload.get("id") # Ensure ID is in the token payload from auth_service

        if username is None or user_email is None or user_id is None:
            raise credentials_exception

        return CurrentUser(username=username, email=user_email, id=user_id)
    except JWTError as e:
        print(f"JWT decoding error in User Service: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error in User Service get_current_user: {e}")
        raise credentials_exception