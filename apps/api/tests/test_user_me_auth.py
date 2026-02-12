def test_me_requires_auth(client):
    r = client.get("/me")
    assert r.status_code == 401, r.text

def test_me_with_debug_uid(client, user_headers):
    r = client.get("/me", headers=user_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["uid"] == "test-user"
    assert body["is_admin"] in (True, False)
