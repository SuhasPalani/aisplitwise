from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.database import get_database
from app.core.rabbitmq import publish_message
from app.models.expense import ExpenseInDB
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdateSplit

# REMOVE THESE TWO LINES:
# from app.api.v1.endpoints.auth import get_current_user # Re-use get_current_user
# from app.schemas.auth import CurrentUser # Re-use CurrentUser

# KEEP THESE TWO LINES (the correct ones):
from app.core.security import get_current_user # <--- Correct import from local security.py
from app.schemas.auth import CurrentUser      # <--- Correct import from local schemas/auth.py

from bson import ObjectId
import json


router = APIRouter()

@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(expense_data: ExpenseCreate, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()

    if not ObjectId.is_valid(expense_data.group_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Group ID format.")

    # Verify group exists and current user is a member
    group_doc = await db["groups"].find_one({"_id": ObjectId(expense_data.group_id)})
    if not group_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    
    if current_user.username not in group_doc["members"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

    # Verify all participants are members of the group
    if not all(p in group_doc["members"] for p in expense_data.participants):
        non_members = [p for p in expense_data.participants if p not in group_doc["members"]]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Some participants are not members of the group: {', '.join(non_members)}"
        )

    # Initially, split is empty. AI Splitter will fill this.
    expense_in_db = ExpenseInDB(
        group_id=ObjectId(expense_data.group_id),
        amount=expense_data.amount,
        paid_by=current_user.username,
        participants=expense_data.participants,
        description=expense_data.description,
        split={} # Initialize empty, AI will update
    )

    result = await db["expenses"].insert_one(expense_in_db.dict(by_alias=True))
    created_expense = await db["expenses"].find_one({"_id": result.inserted_id})
    
    # Publish event to RabbitMQ for AI Splitter
    expense_event_data = {
        "expense_id": str(created_expense["_id"]),
        "group_id": str(created_expense["group_id"]),
        "amount": created_expense["amount"],
        "paid_by": created_expense["paid_by"],
        "participants": created_expense["participants"],
        "description": created_expense["description"]
    }
    await publish_message(
        exchange_name="expense_events",
        routing_key="expense.created",
        message=json.dumps(expense_event_data)
    )

    return ExpenseResponse(
        id=str(created_expense["_id"]),
        group_id=str(created_expense["group_id"]),
        amount=created_expense["amount"],
        paid_by=created_expense["paid_by"],
        participants=created_expense["participants"],
        description=created_expense["description"],
        split=created_expense["split"],
        created_at=created_expense["created_at"].isoformat()
    )

@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense_details(expense_id: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    if not ObjectId.is_valid(expense_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Expense ID format.")

    expense = await db["expenses"].find_one({"_id": ObjectId(expense_id)})
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    
    # Verify user is part of the group associated with the expense
    group_doc = await db["groups"].find_one({"_id": expense["group_id"]})
    if not group_doc or current_user.username not in group_doc["members"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this expense.")

    return ExpenseResponse(
        id=str(expense["_id"]),
        group_id=str(expense["group_id"]),
        amount=expense["amount"],
        paid_by=expense["paid_by"],
        participants=expense["participants"],
        description=expense["description"],
        split=expense["split"],
        created_at=expense["created_at"].isoformat()
    )

@router.get("/groups/{group_id}/expenses", response_model=List[ExpenseResponse])
async def get_group_expenses(group_id: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()

    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Group ID format.")

    group_doc = await db["groups"].find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    if current_user.username not in group_doc["members"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

    expenses = await db["expenses"].find({"group_id": ObjectId(group_id)}).sort("created_at", -1).to_list(None)

    return [
        ExpenseResponse(
            id=str(exp["_id"]),
            group_id=str(exp["group_id"]),
            amount=exp["amount"],
            paid_by=exp["paid_by"],
            participants=exp["participants"],
            description=exp["description"],
            split=exp["split"],
            created_at=exp["created_at"].isoformat()
        ) for exp in expenses
    ]

@router.patch("/expenses/{expense_id}/split", response_model=ExpenseResponse)
async def update_expense_split(expense_id: str, split_data: ExpenseUpdateSplit, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    if not ObjectId.is_valid(expense_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Expense ID format.")

    expense = await db["expenses"].find_one({"_id": ObjectId(expense_id)})
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    
    # Only the user who created the expense or an admin could manually adjust the split (for simplicity, creator only)
    if expense["paid_by"] != current_user.username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this expense's split.")
    
    # Ensure all participants in the new split are part of the expense's original participants
    if not all(p in expense["participants"] for p in split_data.split.keys()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Split includes non-participants.")

    # Ensure total amount in split matches expense amount (allowing for small floating point errors)
    if abs(sum(split_data.split.values()) - expense["amount"]) > 0.01:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total split amount does not match expense amount.")

    update_result = await db["expenses"].update_one(
        {"_id": ObjectId(expense_id)},
        {"$set": {"split": split_data.split}}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes made to expense split or expense not found.")

    updated_expense = await db["expenses"].find_one({"_id": ObjectId(expense_id)})
    return ExpenseResponse(
        id=str(updated_expense["_id"]),
        group_id=str(updated_expense["group_id"]),
        amount=updated_expense["amount"],
        paid_by=updated_expense["paid_by"],
        participants=updated_expense["participants"],
        description=updated_expense["description"],
        split=updated_expense["split"],
        created_at=updated_expense["created_at"].isoformat()
    )

@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    if not ObjectId.is_valid(expense_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Expense ID format.")

    expense = await db["expenses"].find_one({"_id": ObjectId(expense_id)})
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    
    # Only the user who paid for the expense can delete it
    if expense["paid_by"] != current_user.username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this expense.")

    delete_result = await db["expenses"].delete_one({"_id": ObjectId(expense_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    
    return {} # No content for 204