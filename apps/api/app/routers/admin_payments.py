from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.deps import get_current_user, UserContext, require_admin
from app.payments.repo import get_repos

router = APIRouter()

@router.get("/events", response_model=List[Dict[str, Any]])
async def list_payment_events(
    limit: int = 50,
    user: UserContext = Depends(require_admin)
):
    """
    Admin-only endpoint to view recent payment webhook events.
    Includes redacted payloads for debugging without exposing PII.
    """
    repos = get_repos()
    
    # Try fetching with ordering (if index exists) or rely on Python sorting
    # Since we are fetching raw dicts we don't have a strict Pydantic model for the response here
    db = repos.events.db # Access raw db client
    
    events_ref = db.collection(repos.events.collection_name)
    
    try:
        # Attempt to use Firestore ordering
        docs = events_ref.order_by("receivedAt", direction="DESCENDING").limit(limit).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            if "payload" in d:
                del d["payload"] # remove the unredacted structured payload to save bandwidth
            results.append(d)
        return results
    except Exception as e:
        # Fallback if the composite index is missing: fetch limit, sort in python
        # (Firestore default queries on a collection are ordered by __name__, so this isn't strictly newest 
        # if over N docs total exist, but it's an acceptable fallback for local development)
        docs = events_ref.limit(limit).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            if "payload" in d:
                del d["payload"]
            results.append(d)
            
        return sorted(results, key=lambda x: x.get("receivedAt", ""), reverse=True)
