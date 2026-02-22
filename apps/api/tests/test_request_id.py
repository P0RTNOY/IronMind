import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_request_id_middleware_injects_header():
    # Make a simple request to healthz
    response = client.get("/healthz")
    assert response.status_code == 200
    
    # Check that X-Request-Id exists
    assert "X-Request-Id" in response.headers
    assert len(response.headers["X-Request-Id"]) > 0

def test_request_id_middleware_preserves_provided_header():
    # Make a request and manually pass an X-Request-Id
    custom_id = "custom-external-id-12345"
    response = client.get("/healthz", headers={"X-Request-Id": custom_id})
    assert response.status_code == 200
    
    # Check that our provided ID is reflected back
    assert response.headers["X-Request-Id"] == custom_id

def test_request_id_middleware_injects_header_on_error():
    # Request an endpoint that does not exist to ensure middleware catches 404 Exceptions from FastAPI router
    response = client.get("/does-not-exist-route")
    assert response.status_code == 404
    
    # Check that X-Request-Id exists even on HTTP errors
    assert "X-Request-Id" in response.headers
