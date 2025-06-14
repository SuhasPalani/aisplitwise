import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

async def create_dummy_payment_intent(amount: float, currency: str = "usd") -> dict:
    """
    Simulates creating a Stripe PaymentIntent in test mode.
    This will create a PaymentIntent that needs confirmation from the client-side,
    but for backend testing, we are mostly interested in the initial creation.
    """
    try:
        # Amount in cents
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency,
            payment_method_types=["card"], # Can be adjusted
            description=f"Payment for {amount} {currency}"
        )
        return {"id": intent.id, "client_secret": intent.client_secret, "status": intent.status, "amount": amount}
    except stripe.error.StripeError as e:
        print(f"Stripe Error: {e}")
        raise e
    except Exception as e:
        print(f"Unexpected error creating payment intent: {e}")
        raise e

async def confirm_dummy_payment_intent(payment_intent_id: str) -> dict:
    """
    Simulates confirming a Stripe PaymentIntent using a test payment method.
    This is for backend simulation only. In a real app, this is done client-side.
    """
    try:
        # You'd typically use a test payment method ID here (e.g., 'pm_card_visa')
        # For simplicity, we just retrieve and return status, assuming client-side handles confirmation.
        # To truly simulate success, you might want to call stripe.PaymentIntent.confirm
        # with a dummy payment method, but that's more complex for a test.
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # For testing, we'll mark it as successful if it's currently 'requires_payment_method' or 'requires_confirmation'
        # In a real app, this is where you'd integrate the actual payment method ID and confirm
        # Example for direct confirmation for testing purposes:
        # if intent.status in ['requires_payment_method', 'requires_confirmation']:
        #    intent = stripe.PaymentIntent.confirm(payment_intent_id, payment_method="pm_card_visa") # A test card
        
        return {"id": intent.id, "status": intent.status, "amount": intent.amount / 100}
    except stripe.error.StripeError as e:
        print(f"Stripe Error: {e}")
        raise e
    except Exception as e:
        print(f"Unexpected error confirming payment intent: {e}")
        raise e