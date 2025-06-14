from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.database import get_database
from app.core.stripe_api import create_dummy_payment_intent, confirm_dummy_payment_intent
from app.models.payment import PaymentInDB
from app.schemas.payment import PaymentCreate, PaymentResponse, UserBalance, BalanceDue

# REMOVE THESE TWO LINES:
# from auth_service.app.api.v1.endpoints.auth import get_current_user # Re-use get_current_user
# from auth_service.app.schemas.auth import CurrentUser # Re-use CurrentUser

# ADD THESE CORRECT LINES (importing from *this service's* local files):
from app.core.security import get_current_user # Import from YOUR service's local security.py
from app.schemas.auth import CurrentUser      # Import from YOUR service's local schemas/auth.py

from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter()

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payment_data: PaymentCreate, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()

    if current_user.username == payment_data.payee:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot make a payment to yourself.")

    # Check if payee exists (optional, could rely on Auth/User Service for full validation)
    payee_user = await db["users"].find_one({"username": payment_data.payee})
    if not payee_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payee user not found.")

    try:
        # Simulate Stripe PaymentIntent creation
        stripe_intent_info = await create_dummy_payment_intent(payment_data.amount)
        
        payment_in_db = PaymentInDB(
            payer=current_user.username,
            payee=payment_data.payee,
            amount=payment_data.amount,
            method="stripe_test",
            status=stripe_intent_info["status"], # e.g., 'requires_payment_method'
            stripe_payment_intent_id=stripe_intent_info["id"]
        )

        result = await db["payments"].insert_one(payment_in_db.dict(by_alias=True))
        created_payment = await db["payments"].find_one({"_id": result.inserted_id})
        
        return PaymentResponse(
            id=str(created_payment["_id"]),
            payer=created_payment["payer"],
            payee=created_payment["payee"],
            amount=created_payment["amount"],
            method=created_payment["method"],
            status=created_payment["status"],
            stripe_payment_intent_id=created_payment["stripe_payment_intent_id"],
            created_at=created_payment["created_at"].isoformat(),
            completed_at=created_payment["completed_at"].isoformat() if created_payment["completed_at"] else None
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Payment processing error: {e}")


@router.post("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(payment_id: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()

    if not ObjectId.is_valid(payment_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Payment ID format.")

    payment = await db["payments"].find_one({"_id": ObjectId(payment_id)})
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    
    if payment["payer"] != current_user.username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to confirm this payment.")

    if payment["status"] == "succeeded":
        return PaymentResponse(
            id=str(payment["_id"]),
            payer=payment["payer"],
            payee=payment["payee"],
            amount=payment["amount"],
            method=payment["method"],
            status=payment["status"],
            stripe_payment_intent_id=payment["stripe_payment_intent_id"],
            created_at=payment["created_at"].isoformat(),
            completed_at=payment["completed_at"].isoformat() if payment["completed_at"] else None
        )

    try:
        # Simulate Stripe PaymentIntent confirmation (for test mode, just mark as success)
        # In a real app, this would involve client-side confirmation and webhook from Stripe
        # Here we just mark as successful for demonstration
        # stripe_confirmation_info = await confirm_dummy_payment_intent(payment["stripe_payment_intent_id"])

        updated_status = "succeeded" # Force to succeeded for dummy confirmation
        completed_at = datetime.now(timezone.utc)

        update_result = await db["payments"].update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {"status": updated_status, "completed_at": completed_at}}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to confirm payment.")

        updated_payment = await db["payments"].find_one({"_id": ObjectId(payment_id)})
        return PaymentResponse(
            id=str(updated_payment["_id"]),
            payer=updated_payment["payer"],
            payee=updated_payment["payee"],
            amount=updated_payment["amount"],
            method=updated_payment["method"],
            status=updated_payment["status"],
            stripe_payment_intent_id=updated_payment["stripe_payment_intent_id"],
            created_at=updated_payment["created_at"].isoformat(),
            completed_at=updated_payment["completed_at"].isoformat() if updated_payment["completed_at"] else None
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Payment confirmation error: {e}")

@router.get("/payments/history", response_model=List[PaymentResponse])
async def get_payment_history(current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()
    
    payments = await db["payments"].find({
        "$or": [{"payer": current_user.username}, {"payee": current_user.username}]
    }).sort("created_at", -1).to_list(None)

    return [
        PaymentResponse(
            id=str(p["_id"]),
            payer=p["payer"],
            payee=p["payee"],
            amount=p["amount"],
            method=p["method"],
            status=p["status"],
            stripe_payment_intent_id=p["stripe_payment_intent_id"],
            created_at=p["created_at"].isoformat(),
            completed_at=p["completed_at"].isoformat() if p["completed_at"] else None
        ) for p in payments
    ]

@router.get("/balances/{user_id}", response_model=UserBalance)
async def get_user_balances(user_id: str, current_user: CurrentUser = Depends(get_current_user)):
    db = get_database()

    # Note: User_id here should ideally map to username, or current_user.username directly.
    # For simplicity, we'll use current_user.username.
    # In a real system, you might fetch data for any user_id if authenticated and authorized.
    
    username = current_user.username

    # Aggregation pipeline to calculate balances
    # We need to query both expenses and payments collections
    # This example focuses only on payments for simplicity, assuming expenses are settled via payments.
    # A full balance calculation would involve summing up 'split' from expenses and 'amount' from payments.

    # This part needs data from Expense Service to truly reflect balances.
    # For now, we'll calculate based *only* on successful payments.
    # In a fully integrated system, the Reporting Service or a dedicated 'Balance Service'
    # would aggregate data from Expense and Payment services.
    
    # For now, let's simulate a simple balance based on payments recorded here:
    
    pipeline = [
        {"$match": {"$or": [{"payer": username}, {"payee": username}], "status": "succeeded"}},
        {"$group": {
            "_id": None,
            "total_paid_out": {"$sum": {"$cond": [{"$eq": ["$payer", username]}, "$amount", 0]}},
            "total_paid_in": {"$sum": {"$cond": [{"$eq": ["$payee", username]}, "$amount", 0]}},
            "payments_made": {"$push": {"$cond": [{"$eq": ["$payer", username]}, {"payee": "$payee", "amount": "$amount"}, "$$REMOVE"]}},
            "payments_received": {"$push": {"$cond": [{"$eq": ["$payee", username]}, {"payer": "$payer", "amount": "$amount"}, "$$REMOVE"]}},
        }}
    ]

    balance_summary = await db["payments"].aggregate(pipeline).to_list(1)

    owes = 0.0
    owed_by = 0.0
    balances_to_settle: List[BalanceDue] = []
    
    if balance_summary:
        summary = balance_summary[0]
        owes = summary.get("total_paid_out", 0.0)
        owed_by = summary.get("total_paid_in", 0.0)

        # Calculate net amounts owed/owing per individual
        net_individual_balances = {}
        for p in summary.get("payments_made", []):
            net_individual_balances.setdefault(p["payee"], 0.0)
            net_individual_balances[p["payee"]] -= p["amount"] # User paid, so owes less (or other user is owed less)

        for p in summary.get("payments_received", []):
            net_individual_balances.setdefault(p["payer"], 0.0)
            net_individual_balances[p["payer"]] += p["amount"] # User received, so is owed more (or other user owes more)
        
        for other_user, net_amount in net_individual_balances.items():
            if net_amount < 0: # Current user owes 'other_user'
                balances_to_settle.append(BalanceDue(from_user=username, to_user=other_user, amount=abs(net_amount)))
            elif net_amount > 0: # 'other_user' owes current user
                balances_to_settle.append(BalanceDue(from_user=other_user, to_user=username, amount=net_amount))

    net_balance = round(owed_by - owes, 2)

    return UserBalance(
        username=username,
        owes=round(owes, 2),
        owed_by=round(owed_by, 2),
        net_balance=net_balance,
        balances_to_settle=balances_to_settle
    )