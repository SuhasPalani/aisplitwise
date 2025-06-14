from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional # Added Optional as it might be used in schemas/models
from app.core.database import get_database
from app.models.group import GroupInDB
from app.schemas.group import GroupCreate, GroupResponse, AddRemoveMembers, MemberStatus

# REMOVE THESE TWO LINES:
# from app.api.v1.endpoints.auth import get_current_user # Re-use get_current_user
# from app.schemas.auth import CurrentUser # Re-use CurrentUser

# KEEP THESE TWO LINES (the correct ones, importing from *this service's* local files):
from app.core.security import get_current_user # Import from YOUR service's local security.py
from app.schemas.auth import CurrentUser      # Import from YOUR service's local schemas/auth.py

from bson import ObjectId


router = APIRouter()

@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(group_data: GroupCreate, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    # Initial members include the creator
    group_in_db = GroupInDB(
        name=group_data.name,
        members=[current_user.username],
        created_by=current_user.username
    )
    
    result = await db["groups"].insert_one(group_in_db.dict(by_alias=True))
    created_group = await db["groups"].find_one({"_id": result.inserted_id})
    
    return GroupResponse(
        id=str(created_group["_id"]),
        name=created_group["name"],
        members=created_group["members"],
        created_at=created_group["created_at"].isoformat(),
        created_by=created_group["created_by"]
    )

@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group_details(group_id: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Group ID format.")

    group = await db["groups"].find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    
    if current_user.username not in group["members"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

    return GroupResponse(
        id=str(group["_id"]),
        name=group["name"],
        members=group["members"],
        created_at=group["created_at"].isoformat(),
        created_by=group["created_by"]
    )

@router.get("/groups", response_model=List[GroupResponse])
async def get_user_groups(current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    groups = await db["groups"].find({"members": current_user.username}).to_list(None)
    
    return [
        GroupResponse(
            id=str(group["_id"]),
            name=group["name"],
            members=group["members"],
            created_at=group["created_at"].isoformat(),
            created_by=group["created_by"]
        ) for group in groups
    ]

@router.post("/groups/{group_id}/members/add", response_model=MemberStatus)
async def add_group_members(group_id: str, member_data: AddRemoveMembers, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Group ID format.")

    group = await db["groups"].find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    
    # Only group members can add other members
    if current_user.username not in group["members"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to add members to this group.")

    # Validate if all new members exist in the user database (using group service's DB for simplicity here)
    # In a real microservice setup, you'd call the User Service API for this.
    existing_users = await db["users"].find({"username": {"$in": member_data.usernames}}).to_list(None)
    existing_usernames = {u["username"] for u in existing_users}
    
    non_existent_members = [m for m in member_data.usernames if m not in existing_usernames]
    if non_existent_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Some users do not exist: {', '.join(non_existent_members)}"
        )

    update_result = await db["groups"].update_one(
        {"_id": ObjectId(group_id)},
        {"$addToSet": {"members": {"$each": member_data.usernames}}}
    )

    if update_result.modified_count == 0 and not any(m in group["members"] for m in member_data.usernames):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No new members were added or group not found.")

    updated_group = await db["groups"].find_one({"_id": ObjectId(group_id)})
    return MemberStatus(message="Members added successfully.", group_name=updated_group["name"], members=updated_group["members"])


@router.post("/groups/{group_id}/members/remove", response_model=MemberStatus)
async def remove_group_members(group_id: str, member_data: AddRemoveMembers, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Group ID format.")

    group = await db["groups"].find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    
    # Only group members can remove other members
    if current_user.username not in group["members"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to remove members from this group.")

    # Prevent removing the last member or creator if they are the only one left
    if len(group["members"]) == len(member_data.usernames) and all(m in group["members"] for m in member_data.usernames):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove all members from a group. Delete the group instead.")
    
    # Ensure creator is not removed if they are the only one left
    if len(group["members"]) == 1 and group["members"][0] == current_user.username and current_user.username in member_data.usernames:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last member if they are the creator. Delete the group instead.")


    update_result = await db["groups"].update_one(
        {"_id": ObjectId(group_id)},
        {"$pullAll": {"members": member_data.usernames}}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No members were removed or group not found.")
    
    updated_group = await db["groups"].find_one({"_id": ObjectId(group_id)})
    return MemberStatus(message="Members removed successfully.", group_name=updated_group["name"], members=updated_group["members"])

@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Group ID format.")

    group = await db["groups"].find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    
    # Only the creator or an admin (if we had roles) can delete a group
    if group["created_by"] != current_user.username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group creator can delete this group.")

    delete_result = await db["groups"].delete_one({"_id": ObjectId(group_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    
    return {} # No content for 204