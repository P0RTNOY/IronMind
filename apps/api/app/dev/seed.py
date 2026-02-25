"""
Dev-only seed module — creates realistic demo content in Firestore.

CANNOT run in production (ENV == "prod").
Uses fixed document IDs for idempotency.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List

from app.config import settings
from app.repos.firestore import get_db
from app.repos import entitlements

logger = logging.getLogger(__name__)

# ── Fixed demo IDs ──────────────────────────────────────────────────

COURSE_IDS = ["course_demo_one_time", "course_demo_sub"]

COURSE_DATA = {
    "course_demo_one_time": {
        "titleHe": "פרוטוקול כוח בסיסי",
        "descriptionHe": "תוכנית אימונים בסיסית לבניית כוח וסיבולת",
        "type": "one_time",
        "published": True,
        "coverImageUrl": None,
        "tags": ["strength", "beginner"],
    },
    "course_demo_sub": {
        "titleHe": "מסלול חברות - אימון מתקדם",
        "descriptionHe": "גישה מלאה לכל התוכניות והסרטונים עם מנוי חודשי",
        "type": "subscription",
        "published": True,
        "coverImageUrl": None,
        "tags": ["membership", "advanced"],
    },
}

LESSON_TEMPLATES = [
    {
        "titleHe": "שיעור {n} - אימון כוח",
        "descriptionHe": "תרגול בסיסי לבניית כוח פונקציונלי",
        "movementCategory": "Strength",
    },
    {
        "titleHe": "שיעור {n} - מטקון",
        "descriptionHe": "אימון אינטנסיבי לשיפור סיבולת לב ריאה",
        "movementCategory": "Metcon",
    },
    {
        "titleHe": "שיעור {n} - ניידות",
        "descriptionHe": "תרגילי ניידות ושחרור לשיפור טווח תנועה",
        "movementCategory": "Mobility",
    },
]

PLAN_TEMPLATES = [
    {
        "titleHe": "תוכנית אימון שבועית",
        "descriptionHe": "פירוט אימונים לשבוע מלא",
    },
    {
        "titleHe": "מדריך תזונה בסיסי",
        "descriptionHe": "עקרונות תזונה לתמיכה באימונים",
    },
]


def _build_lessons(course_id: str, now: datetime) -> Dict[str, dict]:
    """Return {doc_id: data} for 3 lessons of a course."""
    out = {}
    for n, template in enumerate(LESSON_TEMPLATES, start=1):
        doc_id = f"lesson_demo_{course_id}_{n}"
        data = {
            "courseId": course_id,
            "titleHe": template["titleHe"].format(n=n),
            "descriptionHe": template["descriptionHe"],
            "movementCategory": template["movementCategory"],
            "tags": [template["movementCategory"].lower()],
            "orderIndex": n,
            "published": True,
            "createdAt": now,
            "updatedAt": now,
        }
        # First lesson per course gets a (obviously fake) vimeo ID
        if n == 1:
            data["vimeoVideoId"] = "demo_vimeo_id_123456789"
        else:
            data["vimeoVideoId"] = None
        out[doc_id] = data
    return out


def _build_plans(course_id: str, now: datetime) -> Dict[str, dict]:
    """Return {doc_id: data} for 2 plans of a course."""
    out = {}
    for n, template in enumerate(PLAN_TEMPLATES, start=1):
        doc_id = f"plan_demo_{course_id}_{n}"
        data = {
            "courseId": course_id,
            "titleHe": template["titleHe"],
            "descriptionHe": template["descriptionHe"],
            "tags": [],
            "published": True,
            "createdAt": now,
            "updatedAt": now,
        }
        # First plan per course gets a placeholder PDF path
        if n == 1:
            data["pdfPath"] = "plans/demo/demo.pdf"
        else:
            data["pdfPath"] = None
        out[doc_id] = data
    return out


def _upsert_doc(
    db,
    collection: str,
    doc_id: str,
    data: dict,
    force: bool,
    created: List[str],
    updated: List[str],
    skipped: List[str],
) -> None:
    """Per-doc idempotent upsert."""
    ref = db.collection(collection).document(doc_id)
    snap = ref.get()

    if snap.exists:
        if force:
            data["updatedAt"] = datetime.now(timezone.utc)
            ref.set(data, merge=True)
            updated.append(doc_id)
        else:
            skipped.append(doc_id)
    else:
        ref.set(data)
        created.append(doc_id)


def seed_demo_data(force: bool = False) -> dict:
    """
    Seed realistic demo content into Firestore.

    - Raises RuntimeError in production.
    - Per-doc idempotent: skips existing docs unless force=True.
    - Returns {created: [], updated: [], skipped: []}.
    """
    if settings.ENV == "prod":
        raise RuntimeError("seeding_disabled_in_prod")

    db = get_db()
    now = datetime.now(timezone.utc)

    created: List[str] = []
    updated: List[str] = []
    skipped: List[str] = []

    # ── Courses ─────────────────────────────────────────────────────
    for course_id, course_template in COURSE_DATA.items():
        data = {**course_template, "createdAt": now, "updatedAt": now}
        _upsert_doc(db, "courses", course_id, data, force, created, updated, skipped)

    # ── Lessons (3 per course) ──────────────────────────────────────
    for course_id in COURSE_IDS:
        for doc_id, data in _build_lessons(course_id, now).items():
            _upsert_doc(db, "lessons", doc_id, data, force, created, updated, skipped)

    # ── Plans (2 per course) ────────────────────────────────────────
    for course_id in COURSE_IDS:
        for doc_id, data in _build_plans(course_id, now).items():
            _upsert_doc(db, "plans", doc_id, data, force, created, updated, skipped)

    # ── Optional debug entitlement ──────────────────────────────────
    debug_uid = getattr(settings, "SEED_DEBUG_UID", "")
    if debug_uid:
        try:
            entitlements.upsert_course_entitlement(
                uid=debug_uid,
                course_id="course_demo_one_time",
                source="seed",
            )
            ent_id = f"ent_course_{debug_uid}_course_demo_one_time"
            created.append(ent_id)
            logger.info("Seeded debug entitlement", extra={"uid": debug_uid})
        except Exception as e:
            logger.warning(f"Failed to seed debug entitlement: {e}")

    logger.info(
        "Seed complete",
        extra={
            "created_count": len(created),
            "updated_count": len(updated),
            "skipped_count": len(skipped),
        },
    )

    return {"created": created, "updated": updated, "skipped": skipped}
