import logging
import stripe
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Request, Header, HTTPException, status
from app.config import settings
from app.repos import stripe_events, purchases, entitlements, subscriptions

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(..., alias="Stripe-Signature")):
    """
    Handle Stripe Webhooks.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        payload = await request.body()
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.warning(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event["id"]
    event_type = event["type"]

    # 1. Idempotency Check (Atomic)
    if not stripe_events.create_event_if_absent(event_id, event_type):
        logger.info(f"Event {event_id} already processed. Skipping.")
        return {"status": "skipped", "reason": "idempotent"}

    logger.info(f"Processing event {event_id} type={event_type}")

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(event["data"]["object"])
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(event["data"]["object"])
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(event["data"]["object"])
        else:
            logger.info(f"Unhandled event type: {event_type}")
            
        stripe_events.update_event_status(event_id, "processed")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing webhook {event_id}: {e}", exc_info=True)
        error_msg = f"{type(e).__name__}: {str(e)[:200]}"
        stripe_events.update_event_status(event_id, "failed", error=error_msg)
        # Use 500 to allow Stripe retry logic as we are idempotent
        raise HTTPException(status_code=500, detail="Internal processing error")


async def _handle_checkout_completed(session: dict):
    if session.get("payment_status") != "paid":
        return

    # Extract Metadata
    metadata = session.get("metadata", {})
    client_ref_id = session.get("client_reference_id")
    
    uid = client_ref_id or metadata.get("uid")
    if not uid:
        logger.error("No UID found in session")
        return

    mode = session.get("mode") or ("subscription" if session.get("subscription") else "payment")
    purchase_type = metadata.get("purchaseType")
    # Fallback to mode if purchaseType missing
    if not purchase_type:
        purchase_type = "one_time" if mode == "payment" else "subscription"

    course_id = metadata.get("courseId")
    
    # Record Purchase
    purchases.create_purchase(
        uid=uid,
        stripe_session_id=session["id"],
        amount=session.get("amount_total"),
        currency=session.get("currency"),
        purchase_type=purchase_type,
        course_id=course_id
    )

    # Grant Entitlement
    if mode == "payment" and course_id:
        entitlements.upsert_course_entitlement(uid, course_id)
        
    elif mode == "subscription":
        # Ensure subscription tracking
        sub_id = session.get("subscription")
        
        # Upsert entitlement initially active
        # We don't have expiry yet (it comes in subscription object), 
        # but we assume valid if just paid.
        entitlements.upsert_membership_entitlement(
            uid=uid,
            stripe_subscription_id=sub_id or "",
            status="active",
            expires_at=None # Will be updated by subscription.updated event usually immediately following
        )
        
        if sub_id:
            # Map subscription to user
            subscriptions.upsert_subscription(
                uid=uid,
                stripe_subscription_id=sub_id,
                status="active", # Assume active on payment success
                current_period_end=None, 
                stripe_customer_id=session.get("customer")
            )

async def _handle_subscription_updated(subscription: dict):
    sub_id = subscription["id"]
    status = subscription["status"]
    current_period_end = subscription.get("current_period_end")
    customer = subscription.get("customer")
    metadata = subscription.get("metadata", {})
    
    # Resolve UID
    uid = metadata.get("uid")
    if not uid:
        uid = subscriptions.get_uid_by_subscription_id(sub_id)
    
    if not uid:
        logger.warning(f"Could not resolve UID for subscription {sub_id}")
        return

    # Convert timestamp
    expires_at = None
    if current_period_end:
        expires_at = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

    # Update Subscription Record
    subscriptions.upsert_subscription(
        uid=uid,
        stripe_subscription_id=sub_id,
        status=status,
        current_period_end=expires_at,
        stripe_customer_id=customer
    )
    
    # Entitlement Logic:
    # Always keep entitlement active if we know about it.
    # Access control relies on expiresAt > now.
    # We only set inactive explicitly if deleted/revoked (handled in deleted event).
    
    entitlements.upsert_membership_entitlement(
        uid=uid,
        stripe_subscription_id=sub_id,
        status="active",
        expires_at=expires_at
    )

async def _handle_subscription_deleted(subscription: dict):
    sub_id = subscription["id"]
    metadata = subscription.get("metadata", {})
    uid = metadata.get("uid") or subscriptions.get_uid_by_subscription_id(sub_id)
    
    if not uid:
        return

    # Mark subscription canceled
    current_period_end = subscription.get("current_period_end")
    expires_at = None
    if current_period_end:
        expires_at = datetime.fromtimestamp(current_period_end, tz=timezone.utc)
    
    subscriptions.upsert_subscription(
        uid=uid,
        stripe_subscription_id=sub_id,
        status="deleted",
        current_period_end=expires_at
    )
    
    # Revoke Entitlement
    # User said: "Update membership entitlement... If now >= expiresAt -> status='inactive'"
    # If we just leave it active with an expiresAt, logic holds.
    # But if it's deleted, maybe we want to be sure?
    # Let's check time.
    
    now = datetime.now(timezone.utc)
    is_expired = False
    if expires_at and now >= expires_at:
        is_expired = True
        
    final_status = "inactive" if is_expired else "active"
    
    entitlements.upsert_membership_entitlement(
        uid=uid,
        stripe_subscription_id=sub_id,
        status=final_status,
        expires_at=expires_at
    )
