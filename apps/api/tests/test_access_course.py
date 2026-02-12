from datetime import datetime, timezone, timedelta

def test_access_course_404_if_course_missing(client, user_headers):
    r = client.get("/access/courses/does_not_exist", headers=user_headers)
    assert r.status_code == 404, r.text

def test_access_course_403_when_no_entitlement(client, user_headers, seed_course):
    r = client.get(f"/access/courses/{seed_course}", headers=user_headers)
    assert r.status_code == 403, r.text

def test_access_course_allowed_with_course_entitlement(db, client, user_headers, seed_course, cleanup_docs):
    # Create entitlement doc in real Firestore
    uid = "test-user"
    ent_id = f"ent_course_{uid}_{seed_course}"
    ref = cleanup_docs(db.collection("entitlements").document(ent_id))
    now = datetime.now(timezone.utc)
    ref.set({
        "id": ent_id,
        "uid": uid,
        "kind": "course",
        "courseId": seed_course,
        "status": "active",
        "source": "manual",
        "createdAt": now,
        "updatedAt": now
    })

    r = client.get(f"/access/courses/{seed_course}", headers=user_headers)
    assert r.status_code == 200, r.text
    assert r.json() == {"allowed": True}

def test_access_course_allowed_with_active_membership(db, client, user_headers, seed_course, cleanup_docs):
    uid = "test-user"
    # Create membership entitlement
    ent_id = f"ent_membership_{uid}"
    ref = cleanup_docs(db.collection("entitlements").document(ent_id))
    now = datetime.now(timezone.utc)
    ref.set({
        "id": ent_id,
        "uid": uid,
        "kind": "membership",
        "status": "active",
        "source": "subscription",
        "stripeSubscriptionId": "sub_test",
        "expiresAt": now + timedelta(days=7),
        "updatedAt": now
    })
    
    # Wait briefly for consistency or assume it's immediate (with Firestore immediate consistency largely holds for doc reads by ID)
    
    r = client.get(f"/access/courses/{seed_course}", headers=user_headers)
    assert r.status_code == 200, r.text
    assert r.json() == {"allowed": True}
