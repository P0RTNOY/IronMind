from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.repos.firestore import get_db
import logging

logger = logging.getLogger(__name__)

def write_audit(
    action: str,
    entity_type: str,
    entity_id: str,
    admin_uid: str,
    payload: Optional[Dict[str, Any]] = None
) -> None:
    """
    Write an audit log entry for an admin action.
    Payload is summarized/sanitized to avoid storing huge blobs or secrets.
    """
    db = get_db()
    
    # Sanitize payload
    safe_payload = {}
    if payload:
        for k, v in payload.items():
            # Skip potential secret fields (just in case)
            if "secret" in k.lower() or "token" in k.lower() or "password" in k.lower():
                safe_payload[k] = "***"
            # Truncate long strings
            elif isinstance(v, str) and len(v) > 500:
                safe_payload[k] = v[:500] + "..."
            else:
                safe_payload[k] = v

    audit_entry = {
        "action": action,
        "entityType": entity_type,
        "entityId": entity_id,
        "adminUid": admin_uid,
        "createdAt": datetime.now(timezone.utc),
        "payloadSummary": safe_payload
    }
    
    try:
        db.collection("admin_audit").add(audit_entry)
    except Exception as e:
        # Audit logging should not break the main flow, but we MUST log the failure
        logger.error(f"Failed to write audit log: {e}", exc_info=True)
