"""
Test: PayPlus unmapped event handling (deterministic, monkeypatched).

Verifies:
- Unmapped events are accepted (200 OK), stored, and flagged
- No intent/entitlement/subscription mutations occur for unmapped events
- Duplicate unmapped events are correctly deduped
- Mapped events still flow normally (control test)
"""

import json
from unittest.mock import patch, MagicMock, call

from app.payments import events
from app.payments.service import handle_webhook
from app.payments.provider import VerifiedWebhook


UNMAPPED_HINT = {
    "raw_status_code": "777",
    "raw_status": "pending_review",
    "raw_transaction_type": "unknown_type",
}

UNMAPPED_PAYLOAD = {
    "provider_ref": "pp_req_unmapped_1",
    "transaction_uid": "txn_unmapped_1",
    "raw_status_code": "777",
    "raw_status": "pending_review",
    "unmapped_hint": UNMAPPED_HINT,
}


def _mock_verified_unmapped():
    return VerifiedWebhook(
        provider="payplus",
        event_id="pp_req_unmapped_1:txn_unmapped_1",
        event_type=events.PAYPLUS_UNMAPPED,
        payload=UNMAPPED_PAYLOAD,
    )


def _mock_verified_succeeded():
    return VerifiedWebhook(
        provider="payplus",
        event_id="pp_req_ok_1:txn_ok_1",
        event_type=events.PAYMENT_SUCCEEDED,
        payload={
            "provider_ref": "pp_req_ok_1",
            "transaction_uid": "txn_ok_1",
            "raw_status_code": "000",
            "raw_status": "approved",
        },
    )


def _make_raw_body(payload_dict=None):
    """Build a minimal raw body for handle_webhook."""
    body = payload_dict or {
        "payment_request_uid": "pp_req_unmapped_1",
        "transaction": {
            "uid": "txn_unmapped_1",
            "status_code": "777",
            "status": "pending_review",
            "type": "unknown_type",
        },
    }
    return json.dumps(body).encode("utf-8")


# ── Tests ───────────────────────────────────────────────────────────


class TestUnmappedEventAcceptedAndFlagged:
    """Unmapped events should be stored + flagged but never mutate state."""

    def test_unmapped_event_returns_unmapped_true(self):
        with patch("app.payments.service.get_provider") as mock_get_provider, \
             patch("app.payments.service.get_repos") as mock_get_repos, \
             patch("app.config.settings.PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS", False):

            mock_provider = MagicMock()
            mock_provider.verify_webhook.return_value = _mock_verified_unmapped()
            mock_get_provider.return_value = mock_provider

            mock_repos = MagicMock()
            mock_repos.events.create_event_if_absent.return_value = True
            mock_get_repos.return_value = mock_repos

            result = handle_webhook(_make_raw_body(), headers={"hash": "test"})

            assert result["ok"] is True
            assert result["duplicate"] is False
            assert result["ignored"] is True
            assert result["unmapped"] is True

    def test_unmapped_event_stored_with_flag(self):
        with patch("app.payments.service.get_provider") as mock_get_provider, \
             patch("app.payments.service.get_repos") as mock_get_repos, \
             patch("app.config.settings.PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS", False):

            mock_provider = MagicMock()
            mock_provider.verify_webhook.return_value = _mock_verified_unmapped()
            mock_get_provider.return_value = mock_provider

            mock_repos = MagicMock()
            mock_repos.events.create_event_if_absent.return_value = True
            mock_get_repos.return_value = mock_repos

            handle_webhook(_make_raw_body(), headers={"hash": "test"})

            mock_repos.events.create_event_if_absent.assert_called_once()
            call_kwargs = mock_repos.events.create_event_if_absent.call_args[1]
            event_doc = call_kwargs["event_doc"]

            assert event_doc["unmapped"] is True
            assert event_doc["unmappedHint"] == UNMAPPED_HINT
            assert event_doc["type"] == events.PAYPLUS_UNMAPPED

    def test_unmapped_event_never_mutates_intent(self):
        with patch("app.payments.service.get_provider") as mock_get_provider, \
             patch("app.payments.service.get_repos") as mock_get_repos, \
             patch("app.config.settings.PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS", False):

            mock_provider = MagicMock()
            mock_provider.verify_webhook.return_value = _mock_verified_unmapped()
            mock_get_provider.return_value = mock_provider

            mock_repos = MagicMock()
            mock_repos.events.create_event_if_absent.return_value = True
            mock_get_repos.return_value = mock_repos

            handle_webhook(_make_raw_body(), headers={"hash": "test"})

            # Intent lookup + update should NEVER be called for unmapped events
            mock_repos.intents.find_by_provider_ref.assert_not_called()
            mock_repos.intents.update_intent.assert_not_called()
            mock_repos.subscriptions.upsert_subscription.assert_not_called()


class TestUnmappedEventIdempotency:
    """Duplicate unmapped events should be deduped normally."""

    def test_duplicate_unmapped_returns_duplicate_true(self):
        with patch("app.payments.service.get_provider") as mock_get_provider, \
             patch("app.payments.service.get_repos") as mock_get_repos, \
             patch("app.config.settings.PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS", False):

            mock_provider = MagicMock()
            mock_provider.verify_webhook.return_value = _mock_verified_unmapped()
            mock_get_provider.return_value = mock_provider

            mock_repos = MagicMock()
            mock_repos.events.create_event_if_absent.return_value = False  # duplicate
            mock_get_repos.return_value = mock_repos

            result = handle_webhook(_make_raw_body(), headers={"hash": "test"})

            assert result["ok"] is True
            assert result["duplicate"] is True
            assert "unmapped" not in result  # duplicate short-circuits before unmapped check


class TestMappedEventStillWorks:
    """Control test: mapped events should NOT have unmapped flag."""

    def test_succeeded_event_has_no_unmapped_flag(self):
        with patch("app.payments.service.get_provider") as mock_get_provider, \
             patch("app.payments.service.get_repos") as mock_get_repos, \
             patch("app.config.settings.PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS", False):

            mock_provider = MagicMock()
            mock_provider.verify_webhook.return_value = _mock_verified_succeeded()
            mock_get_provider.return_value = mock_provider

            mock_repos = MagicMock()
            mock_repos.events.create_event_if_absent.return_value = True

            mock_intent = MagicMock()
            mock_intent.id = "pi_control_test"
            mock_intent.uid = "user_control"
            mock_intent.scope = "course"
            mock_intent.courseId = "course_1"
            mock_repos.intents.find_by_provider_ref.return_value = mock_intent
            mock_get_repos.return_value = mock_repos

            result = handle_webhook(
                json.dumps({"payment_request_uid": "pp_req_ok_1", "transaction": {"uid": "txn_ok_1", "status_code": "000", "status": "approved"}}).encode(),
                headers={"hash": "test"},
            )

            assert result["ok"] is True
            assert "unmapped" not in result
            assert result["duplicate"] is False

            # event_doc should have unmapped=False
            call_kwargs = mock_repos.events.create_event_if_absent.call_args[1]
            event_doc = call_kwargs["event_doc"]
            assert event_doc["unmapped"] is False
            assert event_doc["unmappedHint"] is None
