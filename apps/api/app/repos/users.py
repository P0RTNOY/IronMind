from typing import List, Optional, Tuple, Any
from app.repos.firestore import get_db
from app.models import User
from google.cloud.firestore_v1.base_query import FieldFilter
import base64
import json

def _encode_cursor(doc_snapshot: Any) -> str:
    """Encode the last visible document's relevant fields into a cursor string."""
    if not doc_snapshot:
        return None
    data = doc_snapshot.to_dict()
    # We order by lastSeenAt desc, uid asc
    cursor_data = {
        "lastSeenAt": data.get("lastSeenAt").isoformat() if data.get("lastSeenAt") else None,
        "uid": doc_snapshot.id
    }
    return base64.urlsafe_b64encode(json.dumps(cursor_data).encode()).decode()

def _decode_cursor(cursor: str) -> dict:
    """Decode cursor string back to dict."""
    if not cursor:
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(cursor).decode())
    except:
        return None

def list_users(limit: int = 50, cursor: Optional[str] = None) -> Tuple[List[dict], Optional[str]]:
    """
    List users efficiently directly from the 'users' collection.
    Orders by lastSeenAt desc.
    """
    db = get_db()
    query = db.collection("users").order_by("lastSeenAt", direction="DESCENDING")
    
    if cursor:
        cursor_dict = _decode_cursor(cursor)
        if cursor_dict:
            # Only use lastSeenAt for cursor to avoid composite index requirement
            from datetime import datetime
            vals = []
            if cursor_dict.get("lastSeenAt"):
                vals.append(datetime.fromisoformat(cursor_dict["lastSeenAt"]))
            else:
                vals.append(None)
            # Removed uid from vals
            query = query.start_after(vals)

    docs = list(query.limit(limit).stream())
    
    users = []
    for doc in docs:
        d = doc.to_dict()
        d['uid'] = doc.id # Ensure UID is present
        users.append(d)
        
    next_cursor = None
    if len(docs) == limit:
        next_cursor = _encode_cursor(docs[-1])
        
    return users, next_cursor

def get_user(uid: str) -> Optional[dict]:
    db = get_db()
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['uid'] = doc.id
    return data
