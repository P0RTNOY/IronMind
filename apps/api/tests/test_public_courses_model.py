import pytest
from app.models import CoursePublic, Entitlement
from datetime import datetime

# 1. Test Entitlement Deduplication
def test_no_duplicate_entitlement_import_conflicts():
    """
    Sanity check to ensure the canonical Entitlement model can be instantiated
    without throwing runtime errors or missing required fields.
    """
    ent = Entitlement(
        id="ent-123",
        uid="usr-123",
        kind="course",
        status="active",
        source="one_time",
        courseId="course-1"
    )
    assert ent.id == "ent-123"
    assert ent.uid == "usr-123"
    assert ent.kind == "course"
    assert ent.status == "active"
    assert ent.source == "one_time"
    assert ent.courseId == "course-1"
    assert ent.createdAt is None # Optional field
    assert ent.updatedAt is None # Optional field

# 2. Test CoursePublic Extensibility 
def test_course_public_accepts_cover_image_url_and_ignores_extras():
    """
    Ensure the router-level repository extraction successfully maps
    coverImageUrl, tags, and ignores undocumented dict extras from Firestore.
    """
    raw_firestore_doc = {
        "id": "course-1",
        "titleHe": "Test Course",
        "descriptionHe": "A great course",
        "type": "one_time",
        "published": True,
        "coverImageUrl": "https://storage.googleapis.com/bucket/image.jpg",
        "tags": ["fitness", "mobility"],
        "createdAt": datetime(2025, 1, 1),
        "someRandomExtraField": "Should be ignored gracefully"
    }

    # Pydantic parsing natively mimics what happens in fastAPI routes returning the model
    course = CoursePublic(**raw_firestore_doc)

    assert course.id == "course-1"
    assert course.coverImageUrl == "https://storage.googleapis.com/bucket/image.jpg"
    assert course.tags == ["fitness", "mobility"]
    
    # Extra fields shouldn't crash the parser, though they won't be accessible as attributes
    assert not hasattr(course, "someRandomExtraField")
