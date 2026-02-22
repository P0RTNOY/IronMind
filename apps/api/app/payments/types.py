"""
Centralized type aliases for the payments domain.
Prevents string drift across models, repos, and services.
"""

from typing import Literal

IntentKind = Literal["one_time", "subscription"]
IntentScope = Literal["course", "membership"]
IntentStatus = Literal["pending", "succeeded", "failed", "canceled"]
SubscriptionStatus = Literal["active", "past_due", "canceled", "expired"]
