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
from app.config import settings
from app.payments.models import PaymentIntent
from app.payments.provider import VerifiedWebhook
from app.payments.providers.registry import get_provider, get_provider_name
from app.payments.repo import get_repos
from app.payments.redact import redact_payload

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
    provider_name = get_provider_name()
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
        provider=provider_name,
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

    # Update intent with provider ref (repo sets updatedAt internally)
    repos.intents.update_intent(intent.id, {"providerRef": result.provider_ref})

    logger.info(
        "Checkout created",
        extra={
            "intent_id": intent.id,
            "uid": uid,
            "kind": kind,
            "scope": scope,
            "provider": provider_name,
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

    Typed exceptions (WebhookPayloadError, WebhookVerificationError) bubble
    up to the router for correct HTTP status mapping. Only normal outcomes
    return JSON dicts.
    """
    repos = get_repos()
    provider = get_provider()

    # 1. Verify — typed errors bubble to router
    verified: VerifiedWebhook = provider.verify_webhook(raw_body, headers)

    log_ctx = {
        "provider": verified.provider,
        "event_id": verified.event_id,
        "event_type": verified.event_type,
    }

    # 1.5 Optionally Capture Raw Redacted Webhook
    event_doc = {
        "provider": verified.provider,
        "type": verified.event_type,
        "payload": verified.payload,
    }
    
    if settings.PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS:
        try:
            import json
            raw_dict = json.loads(raw_body.decode("utf-8"))
            event_doc["payload_raw_redacted"] = redact_payload(
                raw_dict, set(settings.PAYPLUS_PAYLOAD_REDACT_KEYS)
            )
            event_doc["payload_keys"] = list(raw_dict.keys())[:100]
            if isinstance(raw_dict.get("transaction"), dict):
                event_doc["transaction_keys"] = list(raw_dict["transaction"].keys())[:100]
        except Exception as e:
            logger.warning(f"Failed to parse or redact raw webhook body: {e}")
            event_doc["payload_raw_redacted"] = {"_error": "invalid_json_or_redact_failure"}

    # 2. Idempotency
    created = repos.events.create_event_if_absent(
        provider=verified.provider,
        event_id=verified.event_id,
        event_doc=event_doc,
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
        _handle_payment_succeeded(repos, intent, verified)
        logger.info("Payment succeeded, entitlement granted", extra=log_ctx)

    elif verified.event_type == events.PAYMENT_FAILED:
        repos.intents.update_intent(intent.id, {"status": "failed"})
        logger.info("Payment failed", extra=log_ctx)

    elif verified.event_type == events.SUB_RENEWED:
        _handle_sub_renewed(repos, intent, verified)
        logger.info("Subscription renewed", extra=log_ctx)

    elif verified.event_type == events.SUB_PAST_DUE:
        _handle_sub_past_due(repos, intent, verified)
        logger.info("Subscription past due", extra=log_ctx)

    elif verified.event_type == events.SUB_CANCELED:
        _handle_sub_canceled(repos, intent, verified)
        logger.info("Subscription canceled", extra=log_ctx)

    else:
        logger.info("Unhandled event type, ignoring", extra=log_ctx)
        return {"ok": True, "duplicate": False, "ignored": True}

    return {"ok": True, "duplicate": False}


# ── Helpers ─────────────────────────────────────────────────────────

def _build_subscription_id(
    uid: str,
    provider: str,
    provider_subscription_id: str | None,
    intent_provider_ref: str | None,
) -> str:
    """
    Deterministic subscription ID.
    - With provider_subscription_id: sub_{uid}_{provider}_{id}
    - Without (bootstrap): sub_{uid}_{provider}_bootstrap_{providerRef}
    """
    if provider_subscription_id:
        return f"sub_{uid}_{provider}_{provider_subscription_id}"
    return f"sub_{uid}_{provider}_bootstrap_{intent_provider_ref or 'unknown'}"


def _handle_payment_succeeded(repos, intent: PaymentIntent, verified: VerifiedWebhook) -> None:
    """Mark intent as succeeded and grant the appropriate entitlement."""
    repos.intents.update_intent(intent.id, {"status": "succeeded"})

    from app.repos import entitlements

    if intent.scope == "course" and intent.courseId:
        entitlements.upsert_course_entitlement(
            uid=intent.uid,
            course_id=intent.courseId,
            source="one_time",
        )
    elif intent.scope == "membership":
        provider_sub_id = verified.payload.get("provider_subscription_id")

        # Bootstrap subscription record
        from app.payments.models import Subscription
        sub_id = _build_subscription_id(
            intent.uid, intent.provider, provider_sub_id, intent.providerRef
        )
        repos.subscriptions.upsert_subscription(Subscription(
            id=sub_id,
            uid=intent.uid,
            provider=intent.provider,
            providerSubscriptionId=provider_sub_id or intent.providerRef or "",
            status="active",
        ))

        entitlements.upsert_membership_entitlement(
            uid=intent.uid,
            status="active",
            expires_at=None,
            source="subscription",
            provider=intent.provider,
            provider_subscription_id=provider_sub_id or intent.providerRef or None,
        )


def _handle_sub_renewed(repos, intent: PaymentIntent, verified: VerifiedWebhook) -> None:
    """Subscription renewed — upsert subscription + keep entitlement active."""
    provider_sub_id = verified.payload.get("provider_subscription_id")

    from app.payments.models import Subscription
    sub_id = _build_subscription_id(
        intent.uid, intent.provider, provider_sub_id, intent.providerRef
    )
    repos.subscriptions.upsert_subscription(Subscription(
        id=sub_id,
        uid=intent.uid,
        provider=intent.provider,
        providerSubscriptionId=provider_sub_id or intent.providerRef or "",
        status="active",
    ))

    from app.repos import entitlements
    entitlements.upsert_membership_entitlement(
        uid=intent.uid,
        status="active",
        expires_at=None,
        source="subscription",
        provider=intent.provider,
        provider_subscription_id=provider_sub_id or intent.providerRef or None,
    )


def _handle_sub_past_due(repos, intent: PaymentIntent, verified: VerifiedWebhook) -> None:
    """Subscription past due — update subscription, keep entitlement active for MVP."""
    provider_sub_id = verified.payload.get("provider_subscription_id")

    from app.payments.models import Subscription
    sub_id = _build_subscription_id(
        intent.uid, intent.provider, provider_sub_id, intent.providerRef
    )
    repos.subscriptions.upsert_subscription(Subscription(
        id=sub_id,
        uid=intent.uid,
        provider=intent.provider,
        providerSubscriptionId=provider_sub_id or intent.providerRef or "",
        status="past_due",
    ))

    # MVP: keep entitlement active during past_due (TODO: add grace period logic)
    from app.repos import entitlements
    entitlements.upsert_membership_entitlement(
        uid=intent.uid,
        status="active",
        expires_at=None,
        source="subscription",
        provider=intent.provider,
        provider_subscription_id=provider_sub_id or intent.providerRef or None,
    )
    logger.info("Subscription past_due — entitlement kept active (MVP grace)", extra={
        "uid": intent.uid, "sub_id": sub_id,
    })


def _handle_sub_canceled(repos, intent: PaymentIntent, verified: VerifiedWebhook) -> None:
    """Subscription canceled — update subscription, revoke entitlement."""
    provider_sub_id = verified.payload.get("provider_subscription_id")

    from app.payments.models import Subscription
    sub_id = _build_subscription_id(
        intent.uid, intent.provider, provider_sub_id, intent.providerRef
    )
    repos.subscriptions.upsert_subscription(Subscription(
        id=sub_id,
        uid=intent.uid,
        provider=intent.provider,
        providerSubscriptionId=provider_sub_id or intent.providerRef or "",
        status="canceled",
    ))

    from app.repos import entitlements
    entitlements.upsert_membership_entitlement(
        uid=intent.uid,
        status="inactive",
        expires_at=None,
        source="subscription",
        provider=intent.provider,
        provider_subscription_id=provider_sub_id or intent.providerRef or None,
    )

