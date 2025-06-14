from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.database import get_database
from app.models.user import UserInDB # Used for type hinting/validation (consistency)
from app.schemas.user import UserSearch, FriendRequest, FriendStatus, UserProfile
from app.core.security import get_current_user # Correct import from THIS service's local security.py
from app.schemas.auth import CurrentUser      # Correct import from THIS service's local schemas/auth.py (CurrentUser schema)
from datetime import datetime # Import datetime for created_at if needed for UserProfile

router = APIRouter()

# New endpoint for current user's own profile
@router.get("/me", response_model=UserProfile)
async def read_users_me(current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")

    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")

    # Fetch the full user document from the database using the username from the token
    user_doc = await users_collection.find_one({"username": current_user.username})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in DB for provided token.")
    
    # Ensure correct field names for UserProfile
    return UserProfile(
        username=user_doc["username"],
        email=user_doc["email"],
        friends=user_doc.get("friends", []),
        created_at=user_doc["created_at"].isoformat() # Convert datetime to ISO format string
    )


@router.get("/username/check/{username}", response_model=dict)
async def check_username_availability(username: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")
    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")
    user = await users_collection.find_one({"username": username})
    if user:
        return {"available": False}
    return {"available": True}

@router.get("/username/suggest", response_model=List[str])
async def suggest_usernames(prefix: str, limit: int = 5):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")
    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")
    # Basic suggestion: find usernames starting with prefix
    users = await users_collection.find({"username": {"$regex": f"^{prefix}", "$options": "i"}}).limit(limit).to_list(limit)
    return [user["username"] for user in users]

@router.get("/friends/search", response_model=List[UserSearch])
async def search_users(query: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")
    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")
    # Search for users by username or email, excluding the current user
    results = await users_collection.find(
        {
            "$or": [
                {"username": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}}
            ],
            "username": {"$ne": current_user.username} # Exclude self
        }
    ).limit(10).to_list(10)
    
    return [UserSearch(username=user["username"], email=user["email"]) for user in results]

@router.post("/friends/add", response_model=FriendStatus)
async def add_friend(friend_request: FriendRequest, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")
    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")
    
    # Ensure friend exists
    friend_user = await users_collection.find_one({"username": friend_request.username})
    if not friend_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend not found.")

    # Prevent adding self
    if current_user.username == friend_request.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add yourself as a friend.")

    # Add friend to current user's list if not already present
    update_result = await users_collection.update_one(
        {"username": current_user.username, "friends": {"$ne": friend_request.username}},
        {"$addToSet": {"friends": friend_request.username}}
    )
    
    # Also add current user to friend's list (mutual friendship)
    await users_collection.update_one(
        {"username": friend_request.username, "friends": {"$ne": current_user.username}},
        {"$addToSet": {"friends": current_user.username}}
    )

    if update_result.modified_count == 0:
        # Check if already friends
        current_user_doc = await users_collection.find_one({"username": current_user.username})
        if friend_request.username in current_user_doc.get("friends", []):
            return FriendStatus(message=f"{friend_request.username} is already your friend.", friends=current_user_doc["friends"])
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add friend (unexpected).")

    # Fetch updated friends list for current user
    updated_user_doc = await users_collection.find_one({"username": current_user.username})
    return FriendStatus(message=f"{friend_request.username} added to friends.", friends=updated_user_doc["friends"])


@router.delete("/friends/{username}", response_model=FriendStatus)
async def delete_friend(username: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")
    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")

    # Check if friend exists
    friend_user = await users_collection.find_one({"username": username})
    if not friend_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend not found.")

    # Remove friend from current user's list
    update_result = await users_collection.update_one(
        {"username": current_user.username},
        {"$pull": {"friends": username}}
    )

    # Remove current user from friend's list (mutual deletion)
    await users_collection.update_one(
        {"username": username},
        {"$pull": {"friends": current_user.username}}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{username} is not in your friend list.")

    updated_user_doc = await users_collection.find_one({"username": current_user.username})
    return FriendStatus(message=f"{username} removed from friends.", friends=updated_user_doc["friends"])

@router.get("/me/friends", response_model=List[UserSearch])
async def get_my_friends(current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")
    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")
    user_doc = await users_collection.find_one({"username": current_user.username})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    friend_usernames = user_doc.get("friends", [])
    
    # Fetch details for each friend
    friends_details = await users_collection.find({"username": {"$in": friend_usernames}}).to_list(len(friend_usernames))
    
    return [UserSearch(username=friend["username"], email=friend["email"]) for friend in friends_details]


@router.get("/profile/{username}", response_model=UserProfile)
async def get_user_profile(username: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not initialized")
    users_collection = db["users"]
    if users_collection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Users collection not found in database")
    user_doc = await users_collection.find_one({"username": username})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    return UserProfile(
        username=user_doc["username"],
        email=user_doc["email"],
        friends=user_doc.get("friends", []),
        created_at=user_doc["created_at"].isoformat()
    )