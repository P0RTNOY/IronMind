"""
Provider interface for payment processing.

All providers must implement PaymentProvider.
verify_webhook takes raw bytes + headers (framework-agnostic) to support
real signature verification in Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.payments.models import PaymentIntent


@dataclass(frozen=True)
class ProviderCheckoutResult:
    """Returned by a provider after creating a checkout session."""
    redirect_url: str
    provider_ref: str


@dataclass(frozen=True)
class VerifiedWebhook:
    """Returned by a provider after verifying a webhook payload.

    payload contract (normalized fields providers should include):
      - provider_ref: str       (required — links to PaymentIntent.providerRef)
      - amount: int             (optional — minor units, e.g. 4990 = 49.90)
      - currency: str           (optional — ISO 4217, e.g. "ILS")
      - uid: str                (optional — don't trust; use intent.uid)
      - provider_subscription_id: str (optional — for subscription events)
    """
    provider: str
    event_id: str
    event_type: str   # Must be a canonical type from payments.events
    payload: dict


@runtime_checkable
class PaymentProvider(Protocol):
    """Protocol that every payment provider must implement."""

    def create_one_time_checkout(self, intent: PaymentIntent) -> ProviderCheckoutResult:
        ...

    def create_subscription_checkout(self, intent: PaymentIntent) -> ProviderCheckoutResult:
        ...

    def verify_webhook(
        self,
        raw_body: bytes,
        headers: Mapping[str, str],
    ) -> VerifiedWebhook:
        ...
