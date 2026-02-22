"""
Payments service orchestrator.

Coordinates checkout creation and webhook processing.
Uses the provider interface + repo factory — no direct Stripe calls.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Mapping, Optional

from app.payments import events
from app.payments.models import PaymentIntent
from app.payments.provider import VerifiedWebhook
from app.payments.providers.registry import get_provider
from app.payments.repo import get_repos

logger = logging.getLogger(__name__)


def _generate_intent_id() -> str:
    return f"pi_{uuid.uuid4().hex}"


def create_checkout(
    uid: str,
    kind: str,
    scope: str,
    courseId: Optional[str] = None,
    tier: Optional[str] = None,
) -> dict:
    """
    Create a payment intent and provider checkout session.
    Returns {"url": redirect_url} matching frontend expectations.
    """
    repos = get_repos()
    provider = get_provider()
    now = datetime.now(timezone.utc)

    intent = PaymentIntent(
        id=_generate_intent_id(),
        uid=uid,
        kind=kind,
        scope=scope,
        courseId=courseId,
        tier=tier,
        status="pending",
        provider=provider.__class__.__name__.lower().replace("provider", "") or "stub",
        providerRef=None,
        createdAt=now,
        updatedAt=now,
    )

    # Persist intent
    repos.intents.create_intent(intent)

    # Call provider
    if kind == "one_time":
        result = provider.create_one_time_checkout(intent)
    else:
        result = provider.create_subscription_checkout(intent)

    # Update intent with provider ref
    repos.intents.update_intent(intent.id, {
        "providerRef": result.provider_ref,
        "updatedAt": datetime.now(timezone.utc),
    })

    logger.info(
        "Checkout created",
        extra={
            "intent_id": intent.id,
            "uid": uid,
            "kind": kind,
            "scope": scope,
            "provider": intent.provider,
            "provider_ref": result.provider_ref,
        },
    )

    return {"url": result.redirect_url}


def handle_webhook(
    raw_body: bytes,
    headers: Mapping[str, str],
) -> dict:
    """
    Process an incoming webhook from the active payment provider.

    Steps:
    1. Verify via provider (signature + parse)
    2. Deduplicate via events repo
    3. Locate intent via provider_ref
    4. Route by canonical event type
    5. Grant/revoke entitlements as needed
    """
    repos = get_repos()
    provider = get_provider()

    # 1. Verify
    try:
        verified: VerifiedWebhook = provider.verify_webhook(raw_body, headers)
    except ValueError as exc:
        logger.warning("Webhook verification failed: %s", exc)
        return {"ok": False, "error": str(exc)}

    log_ctx = {
        "provider": verified.provider,
        "event_id": verified.event_id,
        "event_type": verified.event_type,
    }

    # 2. Idempotency
    created = repos.events.create_event_if_absent(
        provider=verified.provider,
        event_id=verified.event_id,
        event_doc={
            "provider": verified.provider,
            "type": verified.event_type,
            "payload": verified.payload,
        },
    )
    if not created:
        logger.info("Duplicate webhook event, skipping", extra=log_ctx)
        return {"ok": True, "duplicate": True}

    # 3. Find intent by provider_ref
    provider_ref = verified.payload.get("provider_ref")
    intent: Optional[PaymentIntent] = None

    if provider_ref:
        intent = repos.intents.find_by_provider_ref(verified.provider, provider_ref)

    if not intent:
        logger.warning("Webhook received but no matching intent found", extra={
            **log_ctx, "provider_ref": provider_ref,
        })
        return {"ok": True, "duplicate": False, "unknown_intent": True}

    log_ctx["intent_id"] = intent.id
    log_ctx["uid"] = intent.uid

    # 4. Route by canonical event type
    if verified.event_type == events.PAYMENT_SUCCEEDED:
        _handle_payment_succeeded(repos, intent)
        logger.info("Payment succeeded, entitlement granted", extra=log_ctx)

    elif verified.event_type == events.PAYMENT_FAILED:
        repos.intents.update_intent(intent.id, {"status": "failed"})
        logger.info("Payment failed", extra=log_ctx)

    else:
        logger.info("Unhandled event type (Phase 0 stub)", extra=log_ctx)

    return {"ok": True, "duplicate": False}


def _handle_payment_succeeded(repos, intent: PaymentIntent) -> None:
    """Mark intent as succeeded and grant the appropriate entitlement."""
    repos.intents.update_intent(intent.id, {"status": "succeeded"})

    # Grant entitlement using existing repos
    from app.repos import entitlements

    if intent.scope == "course" and intent.courseId:
        entitlements.upsert_course_entitlement(
            uid=intent.uid,
            course_id=intent.courseId,
            source="one_time",
        )
    elif intent.scope == "membership":
        entitlements.upsert_membership_entitlement(
            uid=intent.uid,
            stripe_subscription_id=intent.providerRef or "",
            status="active",
            expires_at=None,
            source="subscription",
        )
