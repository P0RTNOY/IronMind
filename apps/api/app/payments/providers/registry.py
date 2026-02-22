"""
Provider registry.

Returns the active PaymentProvider instance based on PAYMENTS_PROVIDER env.
"""

from app.config import settings
from app.payments.provider import PaymentProvider


def get_provider(name: str | None = None) -> PaymentProvider:
    """
    Return a PaymentProvider by name.
    Defaults to settings.PAYMENTS_PROVIDER (usually "stub").
    """
    provider_name = name or settings.PAYMENTS_PROVIDER

    if provider_name == "stub":
        from app.payments.providers.stub import StubProvider
        return StubProvider()

    raise ValueError(f"Unknown payment provider: '{provider_name}'")
