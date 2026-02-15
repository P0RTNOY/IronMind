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
    query = db.collection("users").order_by("lastSeenAt", direction="DESCENDING").order_by("uid")
    
    if cursor:
        cursor_dict = _decode_cursor(cursor)
        if cursor_dict:
            # In a real app we'd construct a snapshot or use start_after values.
            # Firestore python client supports extensive cursor options.
            # For simplicity/robustness without a snapshot, we might need to fetch the doc first 
            # or rely on values if supported.
            # However, start_after(dict) isn't standard. snapshot is best.
            # Let's try fetching the doc by UID to use as cursor if possible, 
            # or use values if strictly ordering by unique fields.
            # Since we order by lastSeenAt (non-unique) + uid (unique), we can use values.
            # BUT: constructing datetime from ISO string is needed.
            from datetime import datetime
            vals = []
            if cursor_dict.get("lastSeenAt"):
                vals.append(datetime.fromisoformat(cursor_dict["lastSeenAt"]))
            else:
                vals.append(None)
            vals.append(cursor_dict["uid"])
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
