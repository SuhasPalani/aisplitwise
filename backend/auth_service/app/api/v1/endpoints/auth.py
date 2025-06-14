from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.database import get_database
from app.models.user import UserInDB
from app.schemas.auth import UserCreate, UserLogin, Token, CurrentUser

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = get_database()
    user_data = await db["users"].find_one({"username": username})
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return CurrentUser(username=user_data["username"], email=user_data["email"], id=str(user_data["_id"]))


@router.post("/signup", response_model=CurrentUser, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    db = get_database()
    
    # Check for unique username
    if await db["users"].find_one({"username": user_data.username}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    
    # Check for unique email
    if await db["users"].find_one({"email": user_data.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)
    user_in_db = UserInDB(
        email=user_data.email,
        username=user_data.username,
        passwordHash=hashed_password
    )
    
    try:
        result = await db["users"].insert_one(user_in_db.dict(by_alias=True))
        created_user = await db["users"].find_one({"_id": result.inserted_id})
        return CurrentUser(username=created_user["username"], email=created_user["email"], id=str(created_user["_id"]))
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username or email already exists.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {e}")


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    user_data = await db["users"].find_one({"username": form_data.username})
    
    if not user_data or not verify_password(form_data.password, user_data["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=CurrentUser)
async def read_users_me(current_user: CurrentUser = Depends(get_current_user)):
    return current_user