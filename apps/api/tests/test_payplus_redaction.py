import pytest
from app.payments.redact import redact_payload

REDACT_KEYS = {"email", "phone", "first_name", "last_name", "card", "pan", "cvv"}

def test_redact_payload_basic_keys():
    payload = {
        "user_id": 123,
        "email": "test@example.com",
        "nested": {
            "First_Name": "John",
            "safe_value": "hello"
        }
    }
    redacted = redact_payload(payload, REDACT_KEYS)
    assert redacted["user_id"] == 123
    assert redacted["email"] == "***redacted***"
    assert redacted["nested"]["First_Name"] == "***redacted***"
    assert redacted["nested"]["safe_value"] == "hello"

def test_redact_payload_heuristics_pan():
    payload = {
        "weird_api_key_for_pan": "4111-1111-1111-1111",
        "clean_pan": "4111111111111111",
        "just_a_number": 4111111111111111, # ints should not match heuristic
        "short_string": "1234",
    }
    redacted = redact_payload(payload, REDACT_KEYS)
    assert redacted["weird_api_key_for_pan"] == "***redacted***"
    assert redacted["clean_pan"] == "***redacted***"
    assert redacted["just_a_number"] == 4111111111111111
    assert redacted["short_string"] == "1234"

def test_redact_payload_heuristics_cvv():
    payload = {
        "security_code": "123",
        "cv_number": "4567",
        "safe_short_string": "999", # key isn't suspicious
        "cvv_field": "123", # 'cvv' is in REDACT_KEYS, caught by basic key check anyway
    }
    redacted = redact_payload(payload, REDACT_KEYS)
    assert redacted["security_code"] == "***redacted***"
    assert redacted["cv_number"] == "***redacted***"
    assert redacted["safe_short_string"] == "999"
    assert redacted["cvv_field"] == "***redacted***"

def test_redact_payload_lists_and_depth():
    payload = {
        "items": [
            {"email": "drop@me.com", "id": 1},
            {"phone": "555-5555", "id": 2}
        ]
    }
    redacted = redact_payload(payload, REDACT_KEYS)
    assert redacted["items"][0]["email"] == "***redacted***"
    assert redacted["items"][0]["id"] == 1
    assert redacted["items"][1]["phone"] == "***redacted***"

def test_redact_payload_truncation():
    long_str = "A" * 600
    payload = {
        "notes": long_str
    }
    redacted = redact_payload(payload, REDACT_KEYS)
    assert len(redacted["notes"]) == 214 # 200 + 14 chars for "...(truncated)"
    assert redacted["notes"].endswith("...(truncated)")
