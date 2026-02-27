import json
import logging
from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.models import WebhookReplayRequest, WebhookReplayResponse
from app.deps import require_admin
from app.payments import service
from app.payments.errors import WebhookPayloadError, WebhookVerificationError, WebhookProcessingError
from app.payments.repo import get_repos

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_PAYLOAD_SIZE = 50 * 1024  # 50KB

def _pick_first(*vals) -> str | None:
    for v in vals:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return None

def _extract_provider_ref(payload: dict) -> str | None:
    """
    Best-effort provider_ref extraction for PayPlus replay payloads.
    Mirrors schema-capture logic: payment_request_uid / page_request_uid can live
    on top-level, in transaction, or under data.
    """
    if not isinstance(payload, dict):
        return None

    tx = payload.get("transaction") if isinstance(payload.get("transaction"), dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    return _pick_first(
        payload.get("payment_request_uid"),
        payload.get("page_request_uid"),
        tx.get("payment_request_uid"),
        tx.get("page_request_uid"),
        data.get("payment_request_uid"),
        data.get("page_request_uid"),
    )

def _classify_mutation_risk(result: dict, intent_found: bool) -> str:
    """
    Conservative classification:
    - safe if ignored/unmapped/duplicate/unknown_intent or intent not found
    - may_mutate otherwise (mapped + intent found)
    """
    if not result:
        return "safe"
    if result.get("duplicate") is True:
        return "safe"
    if result.get("ignored") is True:
        return "safe"
    if result.get("unmapped") is True:
        return "safe"
    if result.get("unknown_intent") is True:
        return "safe"
    if not intent_found:
        return "safe"
    return "may_mutate"

@router.post("/replay", response_model=WebhookReplayResponse)
async def replay_webhook(
    req: WebhookReplayRequest,
    _=Depends(require_admin)
):
    """
    Admin-only endpoint to securely replay a raw JSON payload through the existing
    webhook handler without relying on tunnels or external API keys.
    """
    if req.provider not in {"payplus", "stub"}:
        raise HTTPException(status_code=422, detail="Unsupported provider for replay")

    # 1) Serialize to bytes (compact) and enforce 50KB limit
    raw_body = json.dumps(req.payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(raw_body) > MAX_PAYLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"Payload too large. Max {MAX_PAYLOAD_SIZE} bytes.")

    # 2) Build headers (lowercase keys)
    headers = {"content-type": "application/json"}
    for k, v in req.headers.items():
        headers[k.lower()] = str(v)

    # 3) Inject default hash if missing for payplus
    if req.provider == "payplus":
        if "hash" not in headers and "x-payplus-hash" not in headers and "x-payplus-signature" not in headers:
            headers["hash"] = "replay"

    notes = [f"payload_size_bytes={len(raw_body)}"]

    # 4) Optionally override verify mode
    original_verify_mode = getattr(settings, "PAYPLUS_WEBHOOK_VERIFY_MODE", "log_only")

    # pre-extract provider_ref for intent lookup (best-effort)
    provider_ref = _extract_provider_ref(req.payload) if req.provider == "payplus" else None
    if provider_ref:
        notes.append("provider_ref_extracted")

    try:
        if req.force_log_only and req.provider == "payplus":
            settings.PAYPLUS_WEBHOOK_VERIFY_MODE = "log_only"
            notes.append("verify_mode_forced_log_only")

        # 5) Run through service handler
        result = service.handle_webhook(raw_body, headers)

        # intent lookup (admin-only extra data; does not affect service)
        intent_found = False
        intent_id = None
        intent_status = None

        if req.provider in ("payplus", "stub") and provider_ref:
            try:
                repos = get_repos()
                intent = repos.intents.find_by_provider_ref(req.provider, provider_ref)
                if intent:
                    intent_found = True
                    intent_id = getattr(intent, "id", None) or (intent.get("id") if isinstance(intent, dict) else None)
                    intent_status = getattr(intent, "status", None) or (intent.get("status") if isinstance(intent, dict) else None)
                    notes.append("intent_found")
                else:
                    notes.append("intent_not_found")
            except Exception as exc:
                # Never fail replay due to lookup issues
                logger.warning("Intent lookup failed during replay: %s", exc)
                notes.append("intent_lookup_failed")

        mutation_risk = _classify_mutation_risk(result, intent_found)

        return WebhookReplayResponse(
            ok=bool(result.get("ok")),
            result=result,
            provider=req.provider,
            event_id=result.get("event_id"),
            event_type=result.get("event_type"),
            notes=notes,
            provider_ref=provider_ref,
            intent_found=intent_found,
            intent_id=intent_id,
            intent_status=intent_status,
            mutation_risk=mutation_risk,
        )

    except WebhookVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except WebhookPayloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WebhookProcessingError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Replay processing failed unexpectedly: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error") from exc
    finally:
        # 6) ALWAYS Restore mode
        if req.force_log_only and req.provider == "payplus":
            settings.PAYPLUS_WEBHOOK_VERIFY_MODE = original_verify_mode
