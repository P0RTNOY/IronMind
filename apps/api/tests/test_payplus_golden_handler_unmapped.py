import pytest
import json
from unittest.mock import patch, MagicMock

from app.payments import service
from app.payments import events
from app.payments.provider import VerifiedWebhook
from tests.helpers.fixture_loader import load_json_fixture


def test_handler_safety_for_unmapped_events():
    """
    Safety guard test for unmapped PayPlus webhook events.
    Verifies that unmapped events are short-circuited properly and NEVER 
    mutate state (intents/subscriptions/entitlements).
    """
    payload_dict = load_json_fixture("payplus/unmapped.json")
    raw_body = json.dumps(payload_dict).encode("utf-8")
    
    hint = {
        "raw_status_code": payload_dict["transaction"]["status_code"],
        "raw_status": payload_dict["transaction"]["status"],
        "raw_transaction_type": payload_dict["transaction"]["type"]
    }
    
    mock_verified = VerifiedWebhook(
        provider="payplus",
        event_id=f"{payload_dict['payment_request_uid']}:{payload_dict['transaction']['uid']}",
        event_type=events.PAYPLUS_UNMAPPED,
        payload={
            "provider_ref": payload_dict["payment_request_uid"],
            "unmapped_hint": hint
        },
    )

    with patch("app.payments.service.get_provider") as mock_get_provider, \
         patch("app.payments.service.get_repos") as mock_get_repos, \
         patch("app.config.settings.PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS", False):

        # Setup mock provider to return our VerifiedWebhook
        mock_provider = MagicMock()
        mock_provider.verify_webhook.return_value = mock_verified
        mock_get_provider.return_value = mock_provider

        # Setup mock repos
        mock_repos = MagicMock()
        # Ensure it is not counted as duplicate
        mock_repos.events.create_event_if_absent.return_value = True
        
        # GUARDS: these should raise if called, failing the test instantly!
        mock_repos.intents.update_intent.side_effect = Exception("GUARD FAILURE: update_intent called!")
        mock_repos.subscriptions.upsert_subscription.side_effect = Exception("GUARD FAILURE: upsert_subscription called!")
        
        mock_get_repos.return_value = mock_repos

        with patch("app.repos.entitlements.upsert_membership_entitlement") as mock_entitlements:
            mock_entitlements.side_effect = Exception("GUARD FAILURE: entitlements modified!")
            
            # Action!
            result = service.handle_webhook(raw_body, headers={"hash": "test"})

            # Assert unmapped short-circuit behavior
            assert result["ok"] is True
            assert result["ignored"] is True
            assert result["unmapped"] is True
            assert result["duplicate"] is False

            # Assert event generation happens corectly
            mock_repos.events.create_event_if_absent.assert_called_once()
            call_kwargs = mock_repos.events.create_event_if_absent.call_args[1]
            event_doc = call_kwargs["event_doc"]

            assert event_doc["unmapped"] is True
            assert event_doc["unmappedHint"] == hint
            
            # Double check our mock guards were never triggered
            mock_repos.intents.update_intent.assert_not_called()
            mock_repos.subscriptions.upsert_subscription.assert_not_called()
            mock_entitlements.assert_not_called()
