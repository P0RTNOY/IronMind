"""
Webhook endpoints for payment event processing.

POST /webhooks/payments  — new provider-agnostic handler
POST /webhooks/stripe    — compatibility shim (calls the new handler)
"""

import logging
from fastapi import APIRouter, Request, HTTPException

from app.payments import service as payments_service
from app.payments.errors import (
    WebhookPayloadError,
    WebhookProcessingError,
    WebhookVerificationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/payments")
async def payments_webhook(request: Request):
    """
    Process webhooks from the active payment provider.
    Reads raw body + headers and delegates to payments.service.handle_webhook().
    Typed exceptions map to HTTP statuses: 401, 400, 500.
    """
    raw_body = await request.body()
    headers = dict(request.headers)

    try:
        result = payments_service.handle_webhook(raw_body, headers)
        return result
    except WebhookVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except WebhookPayloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except WebhookProcessingError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/stripe")
async def stripe_webhook_shim(request: Request):
    """
    Legacy Stripe webhook endpoint — compatibility shim.
    Forwards to the new provider-agnostic handler.
    """
    logger.info("Legacy /webhooks/stripe called, forwarding to /webhooks/payments handler")
    return await payments_webhook(request)
