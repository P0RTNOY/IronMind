"""
Payment domain models.

Pydantic v2 models matching project conventions.
All datetimes are timezone-aware UTC. Firestore-serialization friendly.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.payments.types import (
    IntentKind,
    IntentScope,
    IntentStatus,
    SubscriptionStatus,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentIntent(BaseModel):
    """Represents a single checkout attempt."""
    id: str                              # "pi_<uuid>"
    uid: str
    kind: IntentKind
    scope: IntentScope
    courseId: Optional[str] = None
    tier: Optional[str] = None
    status: IntentStatus = "pending"
    provider: str                        # e.g. "stub"
    providerRef: Optional[str] = None    # stable ref returned by provider
    createdAt: datetime = Field(default_factory=_utcnow)
    updatedAt: datetime = Field(default_factory=_utcnow)


class Subscription(BaseModel):
    """Tracks a recurring subscription."""
    id: str                              # "sub_<uuid>"
    uid: str
    provider: str
    providerSubscriptionId: str
    status: SubscriptionStatus = "active"
    currentPeriodEnd: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=_utcnow)
    updatedAt: datetime = Field(default_factory=_utcnow)


class PaymentEvent(BaseModel):
    """Webhook event record for idempotency tracking."""
    id: str                              # "<provider>:<event_id>"
    provider: str
    type: str                            # canonical event type
    receivedAt: datetime = Field(default_factory=_utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)
