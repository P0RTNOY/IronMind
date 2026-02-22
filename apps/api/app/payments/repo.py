"""
Repository factory for the payments module.

Returns a RepoContainer backed by either Firestore or in-memory stores,
controlled by the PAYMENTS_REPO environment variable.

The memory singleton is cached at module level so that FastAPI app and
tests share the exact same store instance within a single process.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.config import settings


@dataclass
class RepoContainer:
    """Holds references to all payment repositories."""
    intents: object
    events: object
    subscriptions: object


_memory_repos: Optional[RepoContainer] = None


def get_repos() -> RepoContainer:
    """
    Return the repo container for the current environment.
    Memory repos are cached as a module-level singleton.
    """
    global _memory_repos

    if settings.PAYMENTS_REPO == "memory":
        if _memory_repos is None:
            from app.payments.repo_memory import (
                MemoryEventsRepo,
                MemoryIntentsRepo,
                MemorySubscriptionsRepo,
            )
            _memory_repos = RepoContainer(
                intents=MemoryIntentsRepo(),
                events=MemoryEventsRepo(),
                subscriptions=MemorySubscriptionsRepo(),
            )
        return _memory_repos

    # Default: Firestore
    from app.payments import repo_events, repo_intents, repo_subscriptions
    return RepoContainer(
        intents=repo_intents,
        events=repo_events,
        subscriptions=repo_subscriptions,
    )
