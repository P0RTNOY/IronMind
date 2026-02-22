"""
Provider registry.

Returns the active PaymentProvider instance based on PAYMENTS_PROVIDER env.
"""

from app.config import settings
from app.payments.provider import PaymentProvider


def get_provider_name(name: str | None = None) -> str:
    """Return the normalized lower-case provider name."""
    return (name or settings.PAYMENTS_PROVIDER or "stub").strip().lower()


def get_provider(name: str | None = None) -> PaymentProvider:
    """
    Return a PaymentProvider by name.
    Defaults to settings.PAYMENTS_PROVIDER (usually "stub").
    """
    provider_name = get_provider_name(name)

    if provider_name == "stub":
        from app.payments.providers.stub import StubProvider
        return StubProvider()

    if provider_name == "payplus":
        from app.payments.providers.payplus import PayPlusProvider
        return PayPlusProvider()

    raise ValueError(f"Unknown payment provider: '{provider_name}'")
