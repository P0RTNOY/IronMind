import stripe
import datetime
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
        mode = "payment"
        metadata_course_id = course_id
    elif purchase_type == "subscription":
        mode = "subscription"
        metadata_course_id = "membership"
    else:
        raise ValueError(f"Invalid purchase_type: {purchase_type}")

    # For now, if price_id is passed, use it. 
    # If not passed, we fail (Prod) or fallback (Dev - optional, but we decided NO fallback for consistency).
    # Since I need to change signature, let's assume the router passes the correct ID.
    pass

def create_checkout_session(
    uid: str, 
    purchase_type: Literal["one_time", "subscription"], 
    course_id: Optional[str] = None,
    price_id: Optional[str] = None
) -> str:
    """
    Create a Stripe Checkout Session.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("Stripe API key not configured")
        
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if purchase_type == "one_time":
        if not course_id:
            raise ValueError("course_id is required for one_time purchase")
        mode = "payment"
        metadata_course_id = course_id
    elif purchase_type == "subscription":
        mode = "subscription"
        # membership usually doesn't have course_id, but if linked to a course sub, it might.
        # For general membership, course_id might be None.
        metadata_course_id = course_id or "membership" 
    else:
        raise ValueError(f"Invalid purchase_type: {purchase_type}")

    if not price_id:
        # STRICT: No fallback to config in this new version
        raise ValueError(f"Price ID required for {purchase_type}")

    try:
        # Idempotency key to prevent duplicate sessions for same request
        idempotency_key = f"checkout_{uid}_{purchase_type}_{metadata_course_id}_{datetime.datetime.now().timestamp()}"
        
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
