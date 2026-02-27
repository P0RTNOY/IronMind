import json
import pytest
from unittest.mock import patch, MagicMock
from app.payments.service import handle_webhook
from app.payments.provider import VerifiedWebhook
from app.payments import events
from tests.test_payplus_golden_mapping import FIXTURE_EXPECTATIONS
from tests.helpers.fixture_loader import load_json_fixture


@pytest.mark.parametrize(
    "fixture_path, expected_event, expected_provider_ref, expected_txn_uid, expected_sub_id",
    FIXTURE_EXPECTATIONS
)
def test_payplus_schema_capture_extraction(
    fixture_path, expected_event, expected_provider_ref, expected_txn_uid, expected_sub_id
):
    """
    Parametrized test over all 6 golden fixtures to ensure schema capture correctly pulls out
    candidates based on expectations per-fixture.
    """
    payload_dict = load_json_fixture(fixture_path)
    raw_body = json.dumps(payload_dict).encode("utf-8")
    
    # Construct a valid VerifiedWebhook that would come from verify_webhook
    mock_verified = VerifiedWebhook(
        provider="payplus",
        event_id=f"{expected_provider_ref}:{expected_txn_uid}" if expected_txn_uid else expected_provider_ref,
        event_type=expected_event,
        payload=payload_dict
    )
    
    with patch("app.payments.service.get_provider") as mock_get_provider, \
         patch("app.payments.service.get_repos") as mock_get_repos, \
         patch("app.config.settings.PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS", True), \
         patch("app.config.settings.PAYPLUS_PAYLOAD_REDACT_KEYS", ["sensitive_pii"]):

        mock_provider = MagicMock()
        mock_provider.verify_webhook.return_value = mock_verified
        mock_get_provider.return_value = mock_provider
        
        mock_repos = MagicMock()
        mock_repos.events.create_event_if_absent.return_value = True
        
        # We don't care about intent updates for this test, dummy it out
        mock_intent = MagicMock()
        mock_repos.intents.find_by_provider_ref.return_value = mock_intent
        
        mock_get_repos.return_value = mock_repos
        
        # Call the service function
        result = handle_webhook(raw_body, headers={"X-Signature": "test"})
        
        # Verify capture was attempted
        mock_repos.events.create_event_if_absent.assert_called_once()
        call_kwargs = mock_repos.events.create_event_if_absent.call_args[1]
        
        event_doc = call_kwargs["event_doc"]
        
        # Extract candidate exactly as expected per fixture
        if expected_provider_ref:
            assert event_doc["providerRefCandidate"] == expected_provider_ref
        else:
            assert not event_doc.get("providerRefCandidate")
            
        if expected_txn_uid:
            assert event_doc["transactionUidCandidate"] == expected_txn_uid
        else:
            assert not event_doc.get("transactionUidCandidate")
            
        if expected_sub_id:
            assert event_doc["providerSubscriptionIdCandidate"] == expected_sub_id
        else:
            assert not event_doc.get("providerSubscriptionIdCandidate")


