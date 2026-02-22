"""
Webhook endpoints for payment event processing.

POST /webhooks/payments  — new provider-agnostic handler
POST /webhooks/stripe    — compatibility shim (calls the new handler)
"""

import logging
from fastapi import APIRouter, Request, HTTPException

from app.payments import service as payments_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/payments")
async def payments_webhook(request: Request):
    """
    Process webhooks from the active payment provider.
    Reads raw body + headers and delegates to payments.service.handle_webhook().
    Returns 200 OK with JSON result.
    """
    raw_body = await request.body()
    headers = dict(request.headers)

    result = payments_service.handle_webhook(raw_body, headers)

    if not result.get("ok"):
        # Verification failed — return 400 so provider knows to stop retrying
        raise HTTPException(status_code=400, detail=result.get("error", "Webhook processing failed"))

    return result


@router.post("/stripe")
async def stripe_webhook_shim(request: Request):
    """
    Legacy Stripe webhook endpoint — compatibility shim.
    Forwards to the new provider-agnostic handler.
    """
    logger.info("Legacy /webhooks/stripe called, forwarding to /webhooks/payments handler")
    return await payments_webhook(request)
