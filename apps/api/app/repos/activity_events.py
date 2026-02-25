"""
Activity events repo — best-effort write + list for observability.

No PII stored. Only uid (opaque ID), resource IDs, and timestamps.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.repos.firestore import get_db

logger = logging.getLogger(__name__)


def write_event(
    event_type: str,
    uid: str,
    course_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    plan_id: Optional[str] = None,
) -> None:
    """Best-effort write. Never raises."""
    try:
        db = get_db()
        doc_id = uuid.uuid4().hex
        db.collection("activity_events").document(doc_id).set({
            "id": doc_id,
            "type": event_type,
            "uid": uid,
            "courseId": course_id,
            "lessonId": lesson_id,
            "planId": plan_id,
            "createdAt": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(f"Failed to write activity event: {e}")


def list_recent(limit: int = 50) -> list:
    """Read recent events, newest first. order_by with Python-sort fallback."""
    db = get_db()
    try:
        from google.cloud.firestore_v1 import Query
        query = (
            db.collection("activity_events")
            .order_by("createdAt", direction=Query.DESCENDING)
            .limit(limit)
        )
        results = [{"id": d.id, **d.to_dict()} for d in query.stream()]
    except Exception:
        # Fallback: fetch without ordering, sort in Python
        query = db.collection("activity_events").limit(limit)
        results = [{"id": d.id, **d.to_dict()} for d in query.stream()]
        results.sort(key=lambda x: str(x.get("createdAt", "")), reverse=True)
    return results
