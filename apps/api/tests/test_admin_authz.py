def test_admin_courses_forbidden_for_non_admin(client, user_headers):
    r = client.get("/admin/courses", headers=user_headers)
    assert r.status_code == 403, r.text

def test_admin_courses_allowed_for_admin(client, admin_headers):
    r = client.get("/admin/courses", headers=admin_headers)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)
