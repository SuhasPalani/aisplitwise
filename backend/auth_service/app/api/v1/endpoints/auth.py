from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.database import get_database
from app.models.user import UserInDB # UserInDB model for type hinting/validation
from app.schemas.auth import UserCreate, UserLogin, Token, CurrentUser
from datetime import timedelta, datetime # Import datetime for created_at

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
    email: str = payload.get("email") # Get email from token payload
    user_id: str = payload.get("id")   # Get ID from token payload

    if username is None or email is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (missing token data)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")

    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")

    # Verify user exists in DB and token data matches
    user_data = await users_collection.find_one({"_id": user_id}) 
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found (from token ID)")
    
    # Optional: cross-check username/email from token with DB data
    if user_data["username"] != username or user_data["email"] != email:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token data mismatch with database record",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(username=user_data["username"], email=user_data["email"], id=str(user_data["_id"]))


@router.post("/signup", response_model=CurrentUser, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")

    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")

    # Check for unique username
    if await users_collection.find_one({"username": user_data.username}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

    # Check for unique email
    if await users_collection.find_one({"email": user_data.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)

    # Create a dictionary directly for insertion to ensure MongoDB generates _id
    user_data_to_insert = {
        "email": user_data.email,
        "username": user_data.username,
        "passwordHash": hashed_password,
        "friends": [], # Initialize friends list
        "created_at": datetime.utcnow() # Set creation timestamp
    }
    
    try:
        result = await users_collection.insert_one(user_data_to_insert)
        created_user = await users_collection.find_one({"_id": result.inserted_id})
        if created_user is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User creation failed unexpectedly.")

        return CurrentUser(username=created_user["username"], email=created_user["email"], id=str(created_user["_id"]))
    except DuplicateKeyError as e:
        # Check if the duplicate key error is on username or email unique index (if defined)
        # This part requires specific index setup in MongoDB for it to be precise.
        # For now, a generic 409 is fine.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username or email already exists.")
    except Exception as e:
        print(f"Error during signup: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred during signup: {e}")

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")

    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")

    user_data = await users_collection.find_one({"username": form_data.username})

    if not user_data or not verify_password(form_data.password, user_data["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        # Pass email and ID to be included in the token payload
        data={"sub": user_data["username"], "email": user_data["email"], "id": str(user_data["_id"])}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=CurrentUser)
async def read_users_me(current_user: CurrentUser = Depends(get_current_user)):
    return current_user