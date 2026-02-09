import stripe
from typing import Optional, Literal
from app.config import settings

def create_checkout_session(
    uid: str, 
    purchase_type: Literal["one_time", "subscription"], 
    course_id: Optional[str] = None
) -> str:
    """
    Create a Stripe Checkout Session and return the URL.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("Stripe API key not configured")
        
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Determine parameters based on type
    if purchase_type == "one_time":
        if not course_id:
            raise ValueError("course_id is required for one_time purchase")
        price_id = settings.STRIPE_PRICE_ID_FUNDAMENTALS_ONE_TIME
        mode = "payment"
        metadata_course_id = course_id
    elif purchase_type == "subscription":
        price_id = settings.STRIPE_PRICE_ID_MEMBERSHIP_MONTHLY
        mode = "subscription"
        metadata_course_id = "membership" # Special flag for webhook
    else:
        raise ValueError(f"Invalid purchase_type: {purchase_type}")

    if not price_id:
        raise RuntimeError(f"Price ID for {purchase_type} not configured")

    try:
        # Idempotency key to prevent duplicate sessions for same request
        idempotency_key = f"checkout_{uid}_{purchase_type}_{metadata_course_id}"
        
        session = stripe.checkout.Session.create(
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode=mode,
            success_url=settings.CHECKOUT_SUCCESS_URL,
            cancel_url=settings.CHECKOUT_CANCEL_URL,
            client_reference_id=uid,
            metadata={
                "uid": uid,
                "courseId": metadata_course_id,
                "purchaseType": purchase_type
            },
            automatic_tax={"enabled": False},
            automatic_payment_methods={"enabled": True},
            idempotency_key=idempotency_key
        )
        
        if not session.url:
            raise RuntimeError("Stripe failed to return a session URL")
            
        return session.url
        
    except stripe.error.StripeError as e:
        raise RuntimeError(f"Stripe API error: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to create checkout session: {str(e)}") from e
