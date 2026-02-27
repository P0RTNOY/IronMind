import pytest
import json
from unittest.mock import patch

from app.payments.providers.payplus import PayPlusProvider
from app.payments import events
from tests.helpers.fixture_loader import load_json_fixture
import json

FIXTURE_EXPECTATIONS = [
    (
        "payplus/approved.json",
        events.PAYMENT_SUCCEEDED,
        "pp_req_ok_001",
        "txn_ok_001",
        None
    ),
    (
        "payplus/declined.json",
        events.PAYMENT_FAILED,
        "pp_req_fail_001",
        "txn_fail_001",
        None
    ),
    (
        "payplus/unmapped.json",
        events.PAYPLUS_UNMAPPED,
        "pp_req_unmapped_001",
        "txn_unmapped_001",
        None
    ),
    (
        "payplus/sub_renewed.json",
        events.SUB_RENEWED,
        "pp_req_sub_renew_001",
        "txn_sub_renew_001",
        "rec_sub_001"
    ),
    (
        "payplus/sub_canceled.json",
        events.SUB_CANCELED,
        "pp_req_sub_cancel_001",
        "txn_sub_cancel_001",
        "rec_sub_001"
    ),
    (
        "payplus/sub_past_due.json",
        events.SUB_PAST_DUE,
        "pp_req_sub_past_due_001",
        "txn_sub_past_due_001",
        "rec_sub_001"
    ),
]


@pytest.mark.parametrize(
    "fixture_path, expected_event, expected_provider_ref, expected_txn_uid, expected_sub_id",
    FIXTURE_EXPECTATIONS
)
def test_payplus_golden_mapping(
    fixture_path, expected_event, expected_provider_ref, expected_txn_uid, expected_sub_id
):
    """
    Test that the PayPlusProvider correctly maps each golden fixture
    to the expected canonical event type and extracts candidates.
    """
    payload_dict = load_json_fixture(fixture_path)
    raw_body = json.dumps(payload_dict).encode("utf-8")
    
    # We use log_only with a dummy signature so it passes verification
    with patch("app.config.settings.PAYPLUS_SECRET_KEY", "test_secret_key"), \
         patch("app.config.settings.PAYPLUS_WEBHOOK_VERIFY_MODE", "log_only"):
         
        provider = PayPlusProvider()
        headers = {"hash": "replay"}
        
        verified = provider.verify_webhook(raw_body, headers)
        
        assert verified is not None
        assert verified.event_type == expected_event
    assert verified.provider == "payplus"
    
    if expected_txn_uid:
        expected_event_id = f"{expected_provider_ref}:{expected_txn_uid}"
    else:
        expected_event_id = expected_provider_ref
        
    assert verified.event_id == expected_event_id
    
    # Check normalized payload fields mapped exactly as expected
    assert verified.payload.get("provider_ref") == expected_provider_ref
    
    if expected_sub_id:
        assert verified.payload.get("provider_subscription_id") == expected_sub_id
    else:
        assert "provider_subscription_id" not in verified.payload
    
    if expected_event == events.PAYPLUS_UNMAPPED:
        assert "unmapped_hint" in verified.payload
        hint = verified.payload["unmapped_hint"]
        assert hint["raw_status_code"] == payload_dict.get("transaction", {}).get("status_code", "")
        assert hint["raw_status"] == payload_dict.get("transaction", {}).get("status", "")
        assert hint["raw_transaction_type"] == payload_dict.get("transaction", {}).get("type", "")
    else:
        assert "unmapped_hint" not in verified.payload
